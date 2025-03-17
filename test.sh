# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

set -e
ROOT_DIR="$(dirname $0)"
BUILD_ARCH="$1"
DISTRO="$2"

if [ -z "$BUILD_ARCH" ]
then
echo "Usage: $0  <BUILD_ARCH> [<DISTRO>]"
exit 1
fi

if [ -z "$DISTRO" ]
then
echo "Usage: $0  [<DISTRO>]"
exit 1
fi

if [ $BUILD_ARCH == "amd64" ]
then
TARGET=ARMHF-${DISTRO^^}
elif [ $BUILD_ARCH == "arm64" ]
then
TARGET=AARCH64-${DISTRO^^}
else
TARGET=$BUILD_ARCH-${DISTRO^^}
fi



if [ ! -d "$ROOT_DIR/TARGET/$TARGET" ]
then
echo "Target directory $TARGET does not exist!"
exit 1
fi

# python tests

python3 -m venv /tmp/testvenv

/tmp/testvenv/bin/python3 -m pip install $ROOT_DIR/build_tools/dpkgdeps_src
/tmp/testvenv/bin/python3 -m unittest discover -s $ROOT_DIR/build_tools/dpkgdeps_src/test/  -p *test.py

IMG_ID=$(uuidgen)

make -C "$ROOT_DIR" base-$BUILD_ARCH TARGET_NAME=$TARGET CROSS_BASE_IMAGE_VER=$DISTRO-slim IMG_TAG=$IMG_ID

make -C "$ROOT_DIR" devc-$BUILD_ARCH  IMG_TAG=$IMG_ID BASE_IMAGE_VER=$IMG_ID CROSS_BASE_IMAGE_VER=$DISTRO-slim

make -C "$ROOT_DIR/test" clean test BASE_IMAGE_REPO=effectiverange/er-devc-$BUILD_ARCH-$DISTRO   BASE_IMAGE_VER=$IMG_ID 







