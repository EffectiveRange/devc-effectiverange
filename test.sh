# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

set -e
BUILD_ARCH="$1"
TARGET="$2"

if [ -z "$BUILD_ARCH" ]
then
echo "Usage: $0  <BUILD_ARCH> [<TARGET>]"
exit 1
fi

if [ -z "$TARGET" ]
then
echo "Usage: $0  [<TARGET>]"
exit 1
fi

DISTRO=$(grep "VERSION_CODENAME=" $(dirname $0)/TARGET/$TARGET/target | cut -d "=" -f 2)

if [ -z "$DISTRO" ]
then
echo "Not able to determine the distro from file $(dirname $0)/TARGET/$TARGET/target"
exit 1
fi

# python tests

python3 -m venv /tmp/testvenv

/tmp/testvenv/bin/python3 -m pip install $(dirname $0)/build_tools/dpkgdeps_src
/tmp/testvenv/bin/python3 -m unittest discover -s $(dirname $0)/build_tools/dpkgdeps_src/test/  -p *test.py

IMG_ID=$(uuidgen)

make -C "$(dirname $0)" base-$BUILD_ARCH TARGET_NAME=$TARGET CROSS_BASE_IMAGE_VER=$DISTRO-slim IMG_TAG=$IMG_ID

make -C "$(dirname $0)" devc-$BUILD_ARCH  IMG_TAG=$IMG_ID BASE_IMAGE_VER=$IMG_ID CROSS_BASE_IMAGE_VER=$DISTRO-slim

make -C "$(dirname $0)/test" clean test BASE_IMAGE_REPO=effectiverange/er-devc-$BUILD_ARCH-$DISTRO   BASE_IMAGE_VER=$IMG_ID 







