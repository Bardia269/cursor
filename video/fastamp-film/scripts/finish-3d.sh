#!/bin/bash
# Rend le 9:16 en parallèle du 16:9 (chaque rendu occupe surtout un cœur pour la 3D),
# puis masterise chaque format dès qu'il est prêt.
cd "$(dirname "$0")/.."
master() {
  ffmpeg -v error -y -i out/raw-$1.mp4 -c:v copy -af "loudnorm=I=-14:TP=-1.5:LRA=9" -c:a aac -b:a 256k -ar 48000 -movflags +faststart out/fastamp-3d-$1.mp4
  ffmpeg -v error -y -i out/raw-$1.mp4 -c:v copy -an -movflags +faststart out/fastamp-3d-$1-sans-son.mp4
  echo "MASTERED $1"
}
( npx remotion render Fastamp-9x16 out/raw-3d-9x16.mp4 --log=error --concurrency=2 --crf=16 && mv out/raw-3d-9x16.mp4 out/raw-9x16.mp4 && master 9x16 ) &
while pgrep -f "remotion render Fastamp-16x9" >/dev/null; do sleep 5; done
master 16x9
wait
echo ALLDONE
