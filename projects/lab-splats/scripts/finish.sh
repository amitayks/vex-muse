#!/bin/bash
# finish.sh <silent.mp4> <music> <duration_s> <out.mp4> [fade_out_s]
# Light film grain + vignette on the picture, music trimmed to the picture with a tail fade, limiter at -1.5 dBFS.
# Master the loudness once, in the mix (see mix_splat_film.sh); do not run a second loudnorm here.
set -e
FF=${FFMPEG:-ffmpeg}
IN=$1; MUS=$2; DUR=$3; OUT=$4; FO=${5:-1.6}
ST=$(python3 -c "print(round($DUR-$FO,3))")
$FF -y -loglevel error -i "$IN" -i "$MUS" -filter_complex \
 "[0:v]noise=alls=2:allf=t,vignette=PI/7,format=yuv420p[v];[1:a]atrim=0:$DUR,asetpts=PTS-STARTPTS,afade=t=out:st=$ST:d=$FO,alimiter=limit=0.84:level=0[a]" \
 -map "[v]" -map "[a]" -t "$DUR" -c:v libx264 -preset medium -crf 17 -pix_fmt yuv420p -c:a aac -b:a 256k -ar 48000 -movflags +faststart "$OUT"
echo "$OUT"
