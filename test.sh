# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

set -e
BUILD_ARCH="$1"
TARGET="$2"

if [ -z "$BUILD_ARCH" ]
then
echo "Usage: $0 <ARCH> [<TARGET>]"
exit 1
fi

if [ $BUILD_ARCH == "arm64" ]
then
TARGET=AARCH64-BULLSEYE
fi

if [ -z "$TARGET" ]
then
TARGET=ARMHF-BULLSEYE
fi

# python tests

python3 -m venv /tmp/testvenv

/tmp/testvenv/bin/python3 -m pip install $(dirname $0)/build_tools/dpkgdeps_src
/tmp/testvenv/bin/python3 -m unittest discover -s $(dirname $0)/build_tools/  -p *test.py

IMG_ID=$(uuidgen)

make -C "$(dirname $0)" base-$BUILD_ARCH TARGET_NAME=$TARGET IMG_TAG=$IMG_ID

make -C "$(dirname $0)" devc-$BUILD_ARCH  IMG_TAG=$IMG_ID BASE_IMAGE_VER=$IMG_ID

make -C "$(dirname $0)/test" clean test BASE_IMAGE_REPO=effectiverange/er-devc-$BUILD_ARCH   BASE_IMAGE_VER=$IMG_ID 







