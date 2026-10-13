#!/bin/bash
# phone.sh <in.mp4> <out.mp4> <w> <h> [target_MiB]
# Two-pass x264 to fit a chat app's upload cap (default 15 MiB, under WhatsApp's 16 MiB), 128k AAC, no extra grain.
# A phone copy is a preview only: the full-quality master still goes to the principal as a file.
set -e; FF=${FFMPEG:-ffmpeg}; FP=${FFPROBE:-ffprobe}
IN=$(realpath "$1"); OUT=$(realpath -m "$2"); W=$3; H=$4; T=${5:-15}
D=$($FP -v error -show_entries format=duration -of csv=p=0 "$IN")
VB=$(python3 -c "print(int(($T*8*1024*1024/$D - 128000)/1000))")
TMP=$(mktemp -d); cd "$TMP"
$FF -y -loglevel error -i "$IN" -vf "scale=$W:$H:flags=lanczos" -c:v libx264 -preset slow -b:v ${VB}k -pass 1 -passlogfile "$TMP/p2" -an -f null -
$FF -y -loglevel error -i "$IN" -vf "scale=$W:$H:flags=lanczos" -c:v libx264 -preset slow -b:v ${VB}k -pass 2 -passlogfile "$TMP/p2" -c:a aac -b:a 128k -movflags +faststart "$OUT"
rm -rf "$TMP"; echo "$OUT $(stat -c %s "$OUT") bytes, video ${VB}k"
