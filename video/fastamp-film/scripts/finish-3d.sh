#!/bin/bash
# Attend le rendu 16:9 en cours, puis rend le 9:16 et masterise les deux.
cd "$(dirname "$0")/.."
while pgrep -f "remotion render Fastamp-16x9" >/dev/null; do sleep 5; done
master() {
  ffmpeg -v error -y -i out/raw-$1.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=9" -c:a aac -b:a 256k -ar 48000 -movflags +faststart out/fastamp-3d-$1.mp4
  ffmpeg -v error -y -i out/raw-$1.mp4 -c:v copy -an -movflags +faststart out/fastamp-3d-$1-sans-son.mp4
  echo "MASTERED $1"
}
master 16x9
npx remotion render Fastamp-9x16 out/raw-9x16.mp4 --log=error --concurrency=4 --crf=16 && master 9x16
echo ALLDONE
