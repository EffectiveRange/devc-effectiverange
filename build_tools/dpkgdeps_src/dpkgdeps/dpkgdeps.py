#!/usr/bin/env -S python3 -u

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import sys
import unittest

import traceback_with_variables
import filelock
import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
import logging
import pathlib
import re
import subprocess
import contextlib
import os
from typing import Optional, Union, Callable
from pathlib import Path as path


def get_logger():
    return logging.getLogger("dpkgdeps")


@contextlib.contextmanager
def pushd(new_dir):
    old_dir = os.getcwd()
    os.chdir(new_dir)
    try:
        yield
    finally:
        os.chdir(old_dir)


depRe = re.compile(r"(?P<name>[^:]+)(?::(?P<arch>\w+))?(?:=(?P<ver>[\w\.\+-]+))?")


def get_os_release():
    with open("/etc/os-release") as f:
        os_release = "".join(f.readlines())
        m = re.match(r".*VERSION_CODENAME=(\w+).*", os_release, re.DOTALL)
        if m is None:
            raise ValueError("Cannot determine OS release")
        return m.group(1)


@dataclass(frozen=True, eq=True)
class Dependency:
    name: str
    ver: Optional[str]
    arch: Optional[str]
    hostinstall: bool

    def specStr(self, arch=True):
        archStr = f":{self.arch}" if self.arch and arch else ""
        verStr = f"={self.ver}" if self.ver else ""
        return f"{self.name}{archStr}{verStr}"

    def retarget(self, target_arch: str):
        if target_arch == self.arch:
            return self
        return Dependency(self.name, self.ver, target_arch, self.hostinstall)

    @staticmethod
    def Parse(s: str, target: str, *, hostinstall=False):
        m = depRe.match(s)
        assert m is not None
        res = m.groupdict()
        return Dependency(
            res["name"], res.get("ver", None), res.get("arch") or target, hostinstall
        )


build_arch = (
    subprocess.run(["dpkg", "--print-architecture"], text=True, stdout=subprocess.PIPE)
    .stdout.splitlines()[0]
    .strip()
)


def parseDependency(entry: Union[str, dict], arch: str) -> Optional[Dependency]:
    if isinstance(entry, str):
        return Dependency.Parse(entry.strip(), arch)
    archs: Union[str, list[str]] = entry.get("arch", arch)
    hostinstall = entry.get("hostinstall", False)
    if (isinstance(archs, str) and arch == archs) or (arch in archs) or hostinstall:
        return Dependency.Parse(entry["name"].strip(), arch, hostinstall=hostinstall)
    return None


def get_deps_impl(deps: dict, key: str, arch: str, distro: str):
    depSet = get_deps_by_key(deps, key, arch)
    distro_deps = deps.get(distro, {})
    return depSet.union(get_deps_by_key(distro_deps, key, arch))
    # NOTE: It's enough to fetch direct dependencies, as if the packaging is correct
    # then there's no need for the transitive dependencies
    # In such case, for now we will add it into deps.json directly


def get_deps_by_key(deps, key, arch):
    depSet: set[Dependency] = set(
        dep for d in deps.get(key, []) if (dep := parseDependency(d, arch)) is not None
    )

    return depSet


def get_ignore_deps(deps, arch):
    ignored = set(Dependency.Parse(d, arch) for d in deps.get("ignore_deps", tuple()))
    return ignored


def get_deps(deps: dict, arch: str, distro: str):
    return get_deps_impl(deps, "deps", arch, distro)


def get_build_deps(deps: dict, arch: str, distro: str):
    return get_deps_impl(deps, "build_deps", arch, distro)


def deb_deps_str(deps: dict, arch: str, distro: str):
    # TODO: add support for versioning!!!
    pkg_deps, _ = retrieve_deps(deps, arch, distro)
    d = sorted(d.name for d in pkg_deps)
    return ",".join(d)


def print_deb_deps(deps: dict, arch: str, distro: str):
    print(deb_deps_str(deps, arch, distro))


def run_in_buildroot(target_arch: str, /, *args):
    if build_arch != target_arch:
        cmd = ["schroot", "-d", "/", "-u", "root", "-c", "buildroot", "--", *args]
    else:
        cmd = hostroot_cmd(args)
    run_cmd(cmd)


def run_in_hostroot(target_arch: str, /, *args):
    cmd = hostroot_cmd(args)
    run_cmd(cmd)


def run_cmd(cmd):
    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    assert p.stdout
    for line in iter(p.stdout.readline, ""):
        get_logger().info(line.replace("\n", "").strip())
    p.stdout.close()
    ret = p.wait()
    if ret != 0:
        raise subprocess.CalledProcessError(ret, cmd)


def hostroot_cmd(args):
    if os.geteuid() == 0:
        cmd = args
    else:
        try:
            subprocess.check_call(["sudo", "-n", "true"])
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "sudo is not available or password-less sudo is not configured "
            )
        cmd = ["sudo", "--", *args]
    return cmd


def run_with_lock(
    target_arch: str,
    callable: Callable[[str], None],
    /,
    *args,
):
    lock = filelock.FileLock("/tmp/dpkgdeps.lock")
    with lock:
        callable(target_arch, *args)


def run_in_buildroot_with_lock(target_arch: str, /, *args):
    run_with_lock(target_arch, run_in_buildroot, *args)


def run_in_hostroot_with_lock(target_arch: str, /, *args):
    run_with_lock(target_arch, run_in_hostroot, *args)


def install_in_root(arch: str, runner, allDeps):
    pkgs = [d.specStr() for d in allDeps]
    runner(arch, "apt", "update")
    runner(
        arch,
        "apt",
        "install",
        "-y",
        *pkgs,
    )


def install_in_buildroot(args, allDeps):
    install_in_root(args.arch, run_in_buildroot_with_lock, allDeps)


def install_in_hostroot(args, allDeps):
    install_in_root(build_arch, run_in_hostroot_with_lock, allDeps)


def main():
    import sys

    sys.stderr.write(f"Invocation:{' '.join(sys.argv)}\n")

    args = get_args()
    setup_logging(args)
    logger = get_logger()
    with traceback_with_variables.printing_exc(
        file_=traceback_with_variables.LoggerAsFile(logger)
    ):
        deps = read_deps_json_recursive(args, pathlib.Path(args.depfiledir))
        if args.list:
            print(json.dumps(deps, indent=2))
            return

        # add ignore from parent to child
        os_release = get_os_release()
        if args.debdeps:
            print_deb_deps(deps, args.arch, os_release)
            return
        all_deps = get_all_dependencies(args.arch, os_release, deps)
        install_in_buildroot(args, all_deps)
        install_in_hostroot(
            args, set(d.retarget(build_arch) for d in all_deps if d.hostinstall)
        )
        if args.arch != build_arch:
            # TODO: factor out build root path as a parameter to script
            run_in_hostroot_with_lock(
                args.arch,
                "/usr/bin/fixbrokenlinks.sh",
                "/var/chroot/buildroot",
            )


def get_all_dependencies(arch: str, distro: str, deps: dict):
    pkg_deps, build_deps = retrieve_deps(deps, arch, distro)
    return pkg_deps.union(build_deps)


def merged_ingores(deps):
    return deps.get("ignore_deps", [])


def setup_logging(args):
    logging.basicConfig()
    logger = get_logger()
    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(args.verbose, len(levels) - 1)]  # cap to last level index
    logger.setLevel(level)


def get_args():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        help="List the collected dependency configuration",
        default=False,
    )
    parser.add_argument(
        "--debdeps",
        help="emit debian package dependency string",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-f",
        "--file",
        help="the default filename to look for as dependency file",
        default="deps.json",
    )
    parser.add_argument(
        "--arch",
        help="the dpgk architecture to use",
        default=build_arch,
    )

    parser.add_argument(
        "--build",
        help="the build output directory",
        default=f"{os.environ.get('HOME','.')}/.erbuild/cache",
    )

    parser.add_argument(
        "--sysroot",
        help="the sysroot path to chroot into",
        default=f"/",
    )
    parser.add_argument(
        "--cachedir",
        help="the cache directory where the local packages are created, and is considered for installation",
        default=f"/opt/debs",
    )
    parser.add_argument(
        "depfiledir",
        help="directory that holds the dependencies file in JSON format",
        # nargs="?",
        # default=f"{os.getcwd()}",
    )

    args = parser.parse_args()
    return args


def cache_paths(args, digest):
    destPath = path(args.cachedir, digest)
    wipPath = path(args.cachedir, f"{digest}.wip")
    return destPath, wipPath


def gen_cache_digest(allDeps):
    digest = hashlib.md5(
        ",".join(sorted(dep.specStr() for dep in allDeps)).encode()
    ).hexdigest()

    return digest


def retrieve_deps(deps, arch: str, distro: str):
    pkgDeps = get_deps(deps, arch, distro)
    buildDeps = get_build_deps(deps, arch, distro)
    return pkgDeps, buildDeps


def concat_elem(old, new):
    if isinstance(old, list) and isinstance(new, list):
        return old + new
    if isinstance(old, dict) and isinstance(new, dict):
        return merge_json(old, new)
    if isinstance(old, list) and len(old) == 0:
        return new
    if isinstance(new, list) and len(new) == 0:
        return old
    raise ValueError(f"Cannot merge {old} and {new}")


def merge_json(old: dict, new: dict):
    return {
        key: concat_elem(old.get(key, []), new.get(key, []))
        for key in set(itertools.chain(old.keys(), new.keys()))
    }


def read_deps_json(args, depDir):
    get_logger().info("Trying to read %s", depDir / args.file)
    if (depDir / args.file).exists():
        with open(os.path.join(depDir, args.file)) as f:
            return json.load(f)
    return {}


def find_files_recursive(args, depDir):
    for root, dirs, files in os.walk(depDir):
        for file in files:
            if file == args.file:
                fpath = os.path.join(root, file)
                get_logger().info("Found %s", fpath)
                with open(fpath) as f:
                    yield json.load(f)


def read_deps_json_recursive(args, depDir):
    import functools

    return functools.reduce(merge_json, find_files_recursive(args, depDir), {})


if __name__ == "__main__":
    main()
