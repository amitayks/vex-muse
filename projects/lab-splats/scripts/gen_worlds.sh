#!/bin/bash
# gen_worlds.sh <project_dir> <world> [<world> ...]
# Generate World Labs Marble worlds (Marble 1.1 Plus) from the project's own stills, in parallel, then pull
# each full-res PLY into the Modal volume (worlds/<project>/<world>.ply) for modal_splat.py renders.
# Input per world: <project_dir>/worlds/src_<world>/source.png (make it with an image model first).
# Output: <project_dir>/worlds/<world>/world.json (+ pano, SPZ, collider) and a log per world.
# Needs WLT_API_KEY (World API credits, separate from Marble-app credits) and Modal tokens.
# Cost: about 1,580-3,080 credits per Plus world; the base is taken at the start (see splat-field-notes).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/../../.." && pwd)"
[ -f "$ROOT/tools/env.sh" ] && source "$ROOT/tools/env.sh"
PY=${PY:-python3}
P="$(cd "$1" && pwd)"; shift; NAME=$(basename "$P")
cd "$P"
for w in "$@"; do
 (
  python3 "$HERE/marble.py" gen --name "$NAME-$w" --model marble-1.1-plus --image "worlds/src_$w/source.png" \
     --out "worlds/$w" --ledger ledger.jsonl --tag "world-$w" > "worlds/$w.gen.log" 2>&1
  url=$(python3 -c "import json;d=json.load(open('worlds/$w/world.json'));print(d.get('ply_url') or '')" 2>/dev/null)
  if [ -n "$url" ]; then
    $PY -m modal run "$HERE/modal_splat.py::url" --url "$url" --dest "worlds/$NAME/$w.ply" >> "worlds/$w.gen.log" 2>&1
    echo "OK $w"
  else
    echo "FAIL $w"; tail -5 "worlds/$w.gen.log"
  fi
 ) &
done
wait
