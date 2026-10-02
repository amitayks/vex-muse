#!/usr/bin/env bash
# Fetch unlicensed upstream references at their pinned commits (study only, never committed).
set -euo pipefail
cd "$(dirname "$0")/.."
pin() { awk -F'|' -v r="$1" '$2 ~ r {gsub(/ /,"",$4); print $4}' vendor/PINS.md; }
if [ ! -d vendor/PDoomVideo ]; then
  git clone --quiet https://github.com/JohnHeibel/PDoomVideo vendor/PDoomVideo
  git -C vendor/PDoomVideo checkout --quiet "$(pin PDoomVideo)" && rm -rf vendor/PDoomVideo/.git
fi
echo "vendor ok"
