#!/bin/bash
# EXAMPLE, NOT A TOOL: the mix of ONE DAY (splat-world-01), a 46 s film of five splat worlds joined by
# dust-wave transitions. The cut times (adelay, duck points), gains and file names belong to that film;
# copy it and change them for a new film. Method (knowledge/references/splat-field-notes.md, Sound):
#  - score ducked ~3 dB around each transition SFX peak;
#  - SFX levelled by K-weighted momentary loudness (ebur128 M), never by RMS of a downsampled copy;
#  - one ambience bed per world, ~14 dB under the score, cross-faded across each cut;
#  - master once here: measure, linear gain to -14 LUFS, limiter; no second loudnorm in the picture finish.
# Inputs in the script folder: take2.mp3 (score), sfx/*.mp3, amb/*.mp3. Output: mix.wav (old one kept as mix_v1.wav).
# ONE DAY mix v2 (critic v1: "no sound design, hollow"; measured swaps sat 2-5 dB UNDER the score).
# score take 2 (ducked -3 dB around each swap peak) + SFX + one ambience bed per world.
# SFX gains set by K-weighted momentary loudness (NOT 8 kHz RMS: these SFX live above 2 kHz):
# each SFX peak (M, 400 ms) ~ -17 LUFS-scale = the music body level, ~5 dB over the ducked score. v1 had them ~10 dB hotter.
# Beds sit ~14 dB under the score (each bed gain = -32 LUFS - its measured I). Cross-fade 1.2 s in, 1.0 s out across cuts.
# Master: measure, linear gain to -14 LUFS, limiter at -1.5 dBFS. Out: audio/mix.wav (old one kept as mix_v1.wav).
set -e; cd "$(dirname "$0")"; FF=${FFMPEG:-ffmpeg}
DUCK="1-0.3*(max(0\,1-abs(t-7.60)/0.6)+max(0\,1-abs(t-18.32)/0.6)+max(0\,1-abs(t-28.94)/0.6)+max(0\,1-abs(t-36.10)/0.6))"
$FF -y -loglevel error -i take2.mp3 -i sfx/open_form.mp3 -i sfx/swap_a.mp3 -i sfx/swap_b.mp3 -i sfx/swap_a.mp3 -i sfx/swap_b.mp3 -i sfx/close_dissolve.mp3 \
 -i amb/roof.mp3 -i amb/alley.mp3 -i amb/crater.mp3 -i amb/port.mp3 -i amb/kiosk.mp3 -filter_complex \
"[0:a]aresample=48000,volume='$DUCK':eval=frame[m];\
[1:a]aresample=48000,highshelf=f=7000:g=-4,lowshelf=f=300:g=4,adelay=0|0,volume=-6.5dB[s1];\
[2:a]aresample=48000,highshelf=f=7000:g=-4,lowshelf=f=300:g=4,adelay=6980|6980,volume=-8dB[s2];\
[3:a]aresample=48000,highshelf=f=7000:g=-4,lowshelf=f=300:g=4,adelay=17660|17660,volume=-7dB[s3];\
[4:a]aresample=48000,highshelf=f=7000:g=-4,lowshelf=f=300:g=4,adelay=28320|28320,volume=-8dB[s4];\
[5:a]aresample=48000,highshelf=f=7000:g=-4,lowshelf=f=300:g=4,adelay=35440|35440,volume=-7dB[s5];\
[6:a]aresample=48000,highshelf=f=7000:g=-4,lowshelf=f=300:g=4,adelay=43800|43800,volume=-7dB[s6];\
[7:a]aresample=48000,atrim=0:9.0,afade=t=in:d=0.6,afade=t=out:st=7.86:d=1.0,volume=12dB,adelay=0|0[b1];\
[8:a]aresample=48000,atrim=0:12.7,afade=t=in:d=1.2,afade=t=out:st=11.68:d=1.0,volume=2dB,adelay=6860|6860[b2];\
[9:a]aresample=48000,atrim=0:12.7,afade=t=in:d=1.2,afade=t=out:st=11.66:d=1.0,volume=15dB,adelay=17540|17540[b3];\
[10:a]aresample=48000,atrim=0:9.2,afade=t=in:d=1.2,afade=t=out:st=8.12:d=1.0,volume=1dB,adelay=28200|28200[b4];\
[11:a]aresample=48000,atrim=0:10.7,afade=t=in:d=1.2,afade=t=out:st=8.68:d=2.0,volume=9.5dB,adelay=35320|35320[b5];\
[m][s1][s2][s3][s4][s5][s6][b1][b2][b3][b4][b5]amix=inputs=12:normalize=0:duration=first,atrim=0:46.0,afade=t=out:st=44.6:d=1.4,aresample=48000" \
 -c:a pcm_f32le /tmp/oneday_premix.wav
I=$($FF -hide_banner -i /tmp/oneday_premix.wav -af ebur128 -f null - 2>&1 | grep "I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(round(-14-($I),2))")
$FF -y -loglevel error -i /tmp/oneday_premix.wav -af "volume=${G}dB,alimiter=limit=0.84:level=0:attack=2:release=60,aresample=48000" -c:a pcm_s16le mix_v2.wav
rm -f /tmp/oneday_premix.wav
[ -f mix_v1.wav ] || cp mix.wav mix_v1.wav
mv mix_v2.wav mix.wav
echo "premix I=$I gain=${G}dB"; $FF -hide_banner -i mix.wav -af ebur128=peak=true -f null - 2>&1 | grep -E "I:|Peak:" | tail -2
