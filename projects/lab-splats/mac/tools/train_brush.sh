#!/bin/bash
# usage: train_brush.sh <tag> <brush binary> <steps flag>   (idempotent: skips when the final PLY exists)
TAG=$1; BIN=$2; STEPFLAG=$3
OUT=~/muse-splats/vol/runs/garden-$TAG; mkdir -p $OUT/ply
LOG=~/muse-splats/logs/train_$TAG.log; MEM=~/muse-splats/logs/mem_$TAG.tsv
if ls $OUT/ply/*30000*.ply >/dev/null 2>&1; then echo "already done"; exit 0; fi
cd ~/muse-splats/data
date +%s > ~/muse-splats/logs/train_$TAG.start
RUST_LOG=info /usr/bin/time -l $BIN ~/muse-splats/data/garden_i4 $STEPFLAG 30000 --eval-split-every 8 --eval-every 5000 \
  --export-every 30000 --export-path $OUT/ply --export-name "garden_${TAG}_{iter}.ply" > $LOG 2>&1 &
TPID=$!
sleep 1; BPID=$(pgrep -P $TPID | head -1)
echo "time_pid=$TPID brush_pid=$BPID" >> $LOG.pids
caffeinate -s -i -w $TPID &
echo -e "epoch\trss_kb\tfootprint\tcpu" > $MEM
while kill -0 $TPID 2>/dev/null; do
  L=$(top -l 1 -pid $BPID -stats pid,mem,cpu 2>/dev/null | tail -1 | awk '{print $2"\t"$3}')
  R=$(ps -o rss= -p $BPID 2>/dev/null | tr -d ' ')
  echo -e "$(date +%s)\t$R\t$L" >> $MEM; sleep 10
done
date +%s > ~/muse-splats/logs/train_$TAG.end
