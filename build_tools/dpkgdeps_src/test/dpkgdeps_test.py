from dpkgdeps import deb_deps_str, get_all_dependencies, retrieve_deps

import unittest
import json


class Test(unittest.TestCase):
    def simple_deps(self):
        text = """
{
    "deps": [
        "libstdc++6",
        "libc6"
    ],
    "build_deps": [
        "libc6-dev"
    ],
    "ignore_deps": [
        "debconf-2.0",
        "libc-dev"
    ]
}
"""
        return json.loads(text)

    def test_simple_parsing(self):

        deps = get_all_dependencies("armhf", self.simple_deps())
        self.assertEqual(len(deps), 3)
        depNames = [d.name for d in deps]
        self.assertIn("libstdc++6", depNames)
        self.assertIn("libc6", depNames)
        self.assertIn("libc6-dev", depNames)
        self.assertTrue(all(d.arch == "armhf" for d in deps))
        self.assertTrue(all(d.ver is None for d in deps))

    def test_simple_debdeps(self):
        deps = deb_deps_str(self.simple_deps(), "armhf")
        self.assertIn("libstdc++6", deps)
        self.assertIn("libc6", deps)

    def complex_deps(self):
        text = """
{
    "deps": [
        "libstdc++6",
        {"name":"libc6","arch":"armhf"}
    ],
    "build_deps": [
        {"name":"libc6-dev","arch":["armhf","arm64"]}
    ],
    "ignore_deps": [
        "debconf-2.0",
        "libc-dev"
    ]
}
"""
        return json.loads(text)

    def complex_deps_w_hostinstall(self):
        text = """
{
    "deps": [
        "libstdc++6",
        {"name":"libc6","arch":"armhf"}
    ],
    "build_deps": [
        {"name":"libc6-dev","arch":["armhf","arm64"]},
        {"name":"protoc-compiler","hostinstall":true}
    ],
    "ignore_deps": [
        "debconf-2.0",
        "libc-dev"
    ]
}
"""
        return json.loads(text)

    def test_complex_parsing_w_hostinstall(self):
        deps = get_all_dependencies("arm64", self.complex_deps_w_hostinstall())
        self.assertEqual(len(deps), 3)
        depNames = [d.name for d in deps]
        self.assertIn("libstdc++6", depNames)
        self.assertIn("libc6-dev", depNames)
        self.assertTrue(all(d.arch == "arm64" for d in deps))
        self.assertTrue(all(d.ver is None for d in deps))
        protod = [d for d in deps if d.name == "protoc-compiler"]
        self.assertEqual(len(protod), 1)
        self.assertTrue(protod[0].hostinstall)

    def test_complex_parsing(self):
        deps = get_all_dependencies("arm64", self.complex_deps())
        self.assertEqual(len(deps), 2)
        depNames = [d.name for d in deps]
        self.assertIn("libstdc++6", depNames)
        self.assertIn("libc6-dev", depNames)
        self.assertTrue(all(d.arch == "arm64" for d in deps))
        self.assertTrue(all(d.ver is None for d in deps))

    def test_complex_parsing_debdeps(self):
        deps = deb_deps_str(self.complex_deps(), "arm64")
        self.assertIn("libstdc++6", deps)
        self.assertNotIn("libc6", deps)

    def test_complex_parsing2(self):
        deps = get_all_dependencies("armhf", self.complex_deps())
        self.assertEqual(len(deps), 3)
        depNames = [d.name for d in deps]
        self.assertIn("libstdc++6", depNames)
        self.assertIn("libc6", depNames)
        self.assertIn("libc6-dev", depNames)
        self.assertTrue(all(d.arch == "armhf" for d in deps))
        self.assertTrue(all(d.ver is None for d in deps))

    def test_complex_parsing2_debdeps(self):
        deps = deb_deps_str(self.complex_deps(), "armhf")
        self.assertIn("libstdc++6", deps)
        self.assertIn("libc6", deps)

    def test_complex_parsing3(self):
        deps = get_all_dependencies("amd64", self.complex_deps())
        self.assertEqual(len(deps), 1)
        depNames = [d.name for d in deps]
        self.assertIn("libstdc++6", depNames)
        self.assertTrue(all(d.arch == "amd64" for d in deps))
        self.assertTrue(all(d.ver is None for d in deps))

    def test_complex_parsing3_debdeps(self):
        deps = deb_deps_str(self.complex_deps(), "amd64")
        self.assertIn("libstdc++6", deps)
        self.assertNotIn("libc6", deps)


if __name__ == "__main__":
    unittest.main()
