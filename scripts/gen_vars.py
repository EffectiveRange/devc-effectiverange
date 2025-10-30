#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT
from dataclasses import dataclass
import itertools
import os
import pathlib
import re
import argparse
from typing import Optional


def_version = {
    "mpfr": "4.2.0",
    "gmp": "6.2.1",
    "mpc": "1.3.1",
    "isl": "0.24",
    "cloog": "0.18.1",
}

parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
for dep, ver in def_version.items():
    parser.add_argument(f"--{dep}", default=ver, type=str, help=f"{dep} version to use")

parser.add_argument("-j", nargs="?", default=1, const=os.cpu_count(), dest="parallel")
parser.add_argument("--newlib", action="store_true", default=False, help="Use newlib")
parser.add_argument(
    "--patchdir", default=None, required=False, help="apply patches from dir"
)

parser.add_argument("--targetdir", default=None, required=False, help="TARGET dir")

parser.add_argument(
    "--langs",
    nargs="+",
    default=["c", "c++"],
    required=False,
    help="List of languages to enable",
)
parser.add_argument("--prefix", type=str, default="/usr", help="The install prefix")


parser.add_argument(
    "--IPv",
    choices=[4, 6],
    type=int,
    nargs="?",
    default=None,
    dest="ipversion",
    help="force IP technology in fetch operations",
)

args = parser.parse_args()

apt_output_re = re.compile(r"(?P<version>(?:\d+\.?)+)(?:-[\w+]+)")


def get_version_from_apt_info(env_var: str):
    var = os.environ.get(env_var, "")
    m = apt_output_re.match(var.split()[1])
    if m:
        return m.groupdict()["version"]
    raise AttributeError(
        f"Version not found from env var '{env_var}' with value '{var}'"
    )


filters = {
    "build",
    "host",
    "target",
    "with-pkgversion",
    "with-bugurl",
    "program-transform-name",
    # NOTE: program suffix causes failure in parameter passing to sub dir configures in gcc
    "program-suffix",
    "enable-nls",
    "enable-bootstrap",
    "enable-multiarch",
    "with-sysroot",
    "prefix",
    "libexecdir",
    "libdir",
    "enable-languages",
}
prefix = str(pathlib.Path(args.prefix).absolute())
replacements = {
    # "prefix": prefix,
    # "libexecdir": f"{prefix}/lib",
    # "libdir": f"{prefix}/lib",
    # "enable-languages": f"{','.join(args.langs)}",
}

gcc_suffix = None
gcc_prefix = None


def sanitize_gcc_options(opts: str):
    def process_opt(opt: str):
        key, *rest = opt.split("=")
        if key == "program-suffix":
            global gcc_suffix
            gcc_suffix = rest[0]
        if key == "program-prefix":
            global gcc_prefix
            gcc_prefix = rest[0]
        val = replacements.get(key, "=".join(r for r in rest if r))
        return "=".join((key, val)) if val else key

    procesed = (
        process_opt(opt.strip())
        for opt in opts.split("--")
        if bool(opt) and all(not opt.startswith(f) for f in filters)
    )
    return " --".join(procesed)


def add_extra_gcc_options(opts: str):
    return " ".join(
        (
            opts,
            "--disable-nls",
            "--disable-bootstrap",
            "--disable-multiarch",
            f"--prefix={prefix}",
            f"--enable-languages={','.join(args.langs)}",
            # NOTE: disable for now, but should be cool to be able
            # to set this up ...
            # f"--with-sysroot={prefix}/{target}",
        )
    )


def remove_patch_ver(ver: str, substitute: Optional[str] = None):
    parts = ver.split(".")[:-1]
    last = [substitute] if substitute else []
    return ".".join(parts + last)


def kernel_url(ver: str):
    url_ver = remove_patch_ver(remove_patch_ver(ver), "x")
    return f"v{url_ver}"


@dataclass(eq=True, frozen=True)
class APTPkgInfo:
    name: str
    arch: str
    repo: str
    pkgver: str


def rpi_source_to_apt(envkey: str):
    src = os.environ.get(f"{envkey}_SOURCE", "").strip()
    pkgver = os.environ.get(f"{envkey}_VER", "").strip()
    if not src or not pkgver:
        return None
    url, spec, arch = src.split()[0:3]
    ver, branch = spec.split("/")[0:2]
    return APTPkgInfo(envkey, arch, f"deb [arch={arch}] {url} {ver} {branch}", pkgver)


def get_apt_sources(s: str, arch: str):
    return set(
        re.sub("^deb ", f"deb [arch={arch}] ", repo) if "arch=" not in repo else repo
        for repo in re.findall('"([^"]+)"', s)
    )


rpi_kernel_ver = os.environ.get("KERNEL_VER") or ""
kernel_ver = rpi_kernel_ver.split("+")[0].split("-")[0]
target = os.environ.get("GCC_MACHINE")

binutils_ver = get_version_from_apt_info("BINUTILS_INFO")
gcc_ver = remove_patch_ver(os.environ.get("GCC_VER", ""), "0")
gcc_major_ver = gcc_ver.split(".")[0]
libc_ver = get_version_from_apt_info("LIBC_INFO")
kernel_arch = os.environ.get("MARCH", "")
gcc_conf = os.environ.get("GCC_CONFIG", "")
glibc_make_flags = os.environ.get("GLIBC_MAKE_FLAGS", "")
gcc_opts = add_extra_gcc_options(sanitize_gcc_options(gcc_conf))
gold_linker = os.environ.get("BINUTILS_GOLD_LINKER", "").strip()
compressed_debuginfo = os.environ.get("LD_COMPRESSED_DEBUGINFO", "").strip()
gold_default = os.environ.get("LD_DEFAULT_GOLD", "").strip()
debootstrap_source = os.environ.get("DEBOOTSRAP_SOURCE", "").strip().rstrip("/")
debootsrap_target = os.environ.get("VERSION_CODENAME", "").strip()
rpi_kernel_vers = (
    os.environ.get("RPI_KERNEL_VER_LIST", "").strip().strip(",").split(",")
)

pkgInfos = [
    info for key in ("RPI_KERNEL_HEADERS", "LIBC6") if (info := rpi_source_to_apt(key))
]
arches = {i.arch for i in pkgInfos}
assert len(arches) == 1, "Multiple architecture deteceted"
rpi_apt_arch = tuple(arches)[0]
pkgRepos = get_apt_sources(os.environ.get("APT_SOURCES", "").strip(), rpi_apt_arch)

targetPkgRepos = [p for p in pkgRepos if debootstrap_source not in p]


rpi_apt_archive_key = os.environ.get("RPI_APT_ARCHIVE_KEY", "").strip()
rpi_apt_key = os.environ.get("RPI_APT_KEY", "").strip()


def quoted(s: str):
    return f'"{s}"'


def printPkgVars(pkg: APTPkgInfo):
    print(f"{pkg.name}_VERSION={quoted(pkg.pkgver)}")


kernel_arch_mapping = {"aarch64": "arm64"}

print(
    f"""
TARGET={target}
BINUTILS_VERSION={binutils_ver}
GCC_VERSION={gcc_ver}
GCC_MAJOR_VERSION={gcc_major_ver}
GLIBC_VERSION={libc_ver}
LINUX_ARCH={"arm" if kernel_arch.startswith("arm") else kernel_arch_mapping.get(kernel_arch,kernel_arch)}
LINUX_KERNEL_VERSION={kernel_ver}
LINUX_KERNEL_MINOR_VERSION={'.'.join(rpi_kernel_ver.split('.')[:2])}
LINUX_KERNEL_VERSION_URL={kernel_url(kernel_ver)}
RPI_APT_SOURCES=({' '.join(quoted(r) for r in sorted(pkgRepos))})
RPI_APT_KEYS=({rpi_apt_archive_key} {rpi_apt_key})
RPI_APT_ARCH="{rpi_apt_arch}"
RPI_KERNEL_VERSION={rpi_kernel_ver}
PARALLEL_MAKE=-j{args.parallel} #ignore-hash
USE_NEWLIB={1 if args.newlib else 0}
INSTALL_PATH="{prefix}"
GCC_CONFIGURATION_OPTIONS="{gcc_opts}"
GLIBC_MAKE_FLAGS="{glibc_make_flags}"
DEBOOTSTRAP_SOURCE="{debootstrap_source}"
DEBOOTSTRAP_TARGET="{debootsrap_target}"
TARGET_APT_SOURCES=({' '.join(quoted(r) for r in sorted(targetPkgRepos))})
RPI_KERNEL_HDR_VERSIONS=({' '.join(quoted(r) for r in sorted(rpi_kernel_vers))})
"""
)

for pkg in pkgInfos:
    printPkgVars(pkg)

if gcc_suffix:
    print(f"GCC_SUFFIX={gcc_suffix}")

binutils_config_options = ""

if gcc_prefix:
    print(f"PROGRAM_PREFIX={gcc_prefix}")
    binutils_config_options += f" --program-prefix={gcc_prefix}"

if compressed_debuginfo:
    binutils_config_options += " --enable-compressed-debug-sections=all"

if gold_linker:
    binutils_config_options += f' --enable-gold={"default" if gold_default else "yes" }'

if gold_linker and not gold_default:
    binutils_config_options += " --enable-ld=default"

print(f'BINUTILS_CONFIGURATION_OPTIONS="{binutils_config_options}"')

if args.patchdir:
    print(f"TARGET_PATCH_DIR={args.patchdir} #ignore-hash")

if args.targetdir:
    print(f"TARGET_DIR={args.targetdir} #ignore-hash")

if args.ipversion is not None:
    inet_ver = "--inet4-only" if args.ipversion == 4 else "--inet6-only"
    print(f"WGET_IP_VER={inet_ver}")

for dep in def_version.keys():
    print(f"{dep.upper()}_VERSION={getattr(args,dep)}")
