#!/bin/bash
set -e  -o pipefail

STEP_DESCRIPTION="testing build and packaging toolchain"

DEB_ARCH=$(grep CPACK_DEBIAN_PACKAGE_ARCHITECTURE /usr/share/cmake/toolchain.cmake  | sed -r 's/.*CPACK_DEBIAN_PACKAGE_ARCHITECTURE (\w+).*/\1/g')

TEST_DIR=$(dirname $0)

rm -rf /tmp/build/build_exe_test
mkdir -p /tmp/build/build_exe_test
cd /tmp/build/build_exe_test
xcmake "$TEST_DIR/build_exe_test"
cmake --build .
ctest .
cpack .
dpkg -c /opt/debs/test_exe_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/bin/test$"
dpkg -I /opt/debs/test_exe_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*openssl.*$"
dpkg -I /opt/debs/test_exe_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libstdc\+\+6.*$"
dpkg -I /opt/debs/test_exe_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libc6.*$"


rm -rf /tmp/build/build_shared_lib_test
mkdir -p  /tmp/build/build_shared_lib_test
cd /tmp/build/build_shared_lib_test
xcmake "$TEST_DIR/build_shared_lib_test"
cmake --build .
ctest .
cpack .
dpkg -c /opt/debs/test_sharedlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/lib/libtest_sharedlib.so$"
dpkg -c /opt/debs/test_sharedlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/include/test_shared_lib/test.hpp$"
dpkg -I /opt/debs/test_sharedlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libstdc\+\+6.*$"
dpkg -I /opt/debs/test_sharedlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libc6.*$"


rm -rf /tmp/build/build_static_lib_test
mkdir -p  /tmp/build/build_static_lib_test
cd /tmp/build/build_static_lib_test
xcmake "$TEST_DIR/build_static_lib_test"
cmake --build .
ctest .
cpack .
dpkg -c /opt/debs/test_staticlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/bin/libtest_slib.a$"
dpkg -c /opt/debs/test_staticlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/include/test_lib/test.hpp$"
nodepends="$(dpkg -I /opt/debs/test_staticlib_build_1.0.0-1_${DEB_ARCH}.deb | grep -E 'Depends:' || true)"
if [ -n "$nodepends" ]; then
  echo "ERROR: static library should not have dependencies"
  exit 1
fi


rm -rf /tmp/build/build_complex_test
mkdir -p  /tmp/build/build_complex_test
cd /tmp/build/build_complex_test
xcmake "$TEST_DIR/build_complex_test"
cmake --build .
ctest .
cpack .
dpkg -c /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/bin/complexbin$"
dpkg -c /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/bin/libcomplexlib.a$"
dpkg -c /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "./usr/local/include/complexlib/lib.hpp$"
dpkg -I /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libncurses6.*$"
dpkg -I /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libstdc\+\+6.*$"
dpkg -I /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libc6.*$"

# Test for complex dep specification
if [ $DEB_ARCH = "armhf" ]; then
  dpkg -I /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libpigpio1.*$"
else
  if dpkg -I /opt/debs/test_complex_build_1.0.0-1_${DEB_ARCH}.deb | grep -E "Depends:.*libpigpio1.*$" ; then
    echo "ERROR: libpigpio1 should not be a dependency only on armhf"
    exit 1
  fi
fi
