#!/bin/bash
# usage: scripts/check.sh COMP "f1,f2,..." cols
set -e
COMP=$1; FR=$2; COLS=${3:-3}
rm -rf out/check/$COMP && mkdir -p out/check/$COMP
npx remotion render $COMP out/check/$COMP --frames=$FR --image-format=jpeg --log=error >/dev/null
ffmpeg -v error -y -pattern_type glob -i "out/check/$COMP/element-*.jpeg" -vf "scale=640:-1,tile=${COLS}x3" out/check/${COMP}-sheet.png
echo out/check/${COMP}-sheet.png
