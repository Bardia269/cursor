#!/bin/bash
# Rendu final des deux formats + mastering audio (-14 LUFS, -1 dBTP) + versions sans son.
set -e
cd "$(dirname "$0")/.."
for F in 16x9 9x16; do
  npx remotion render Fastamp-$F out/raw-$F.mp4 --log=error --concurrency=4 --crf=16
  ffmpeg -v error -y -i out/raw-$F.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=9" -c:a aac -b:a 256k -ar 48000 -movflags +faststart out/fastamp-$F.mp4
  ffmpeg -v error -y -i out/raw-$F.mp4 -c:v copy -an -movflags +faststart out/fastamp-$F-sans-son.mp4
  echo "rendered $F"
done
echo ALLDONE
