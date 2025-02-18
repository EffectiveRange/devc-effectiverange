#!/bin/bash

BUILD_ROOT=$1

if [ ! -d "$BUILD_ROOT" ]; then
    echo "Error: $BUILD_ROOT is not a directory"
    echo "Usage: $0  <buildroot>"
    exit 1
fi


BROKEN_LINKS=$(find $BUILD_ROOT -xtype l -name *.so)

for LINK in $BROKEN_LINKS; do
    TARGET=$(readlink $LINK)
    NEW_TARGET=$(realpath -s --relative-to=$(dirname $LINK) $BUILD_ROOT/$TARGET)
    if [ -z "$NEW_TARGET" ]; then
        echo "Error: Could not find target for $LINK"
        exit 1
    fi
    ln -svf $NEW_TARGET $LINK
done