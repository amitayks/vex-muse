#!/usr/bin/env bash
# build_driver.sh [shaders-version] — rebuild assets/driver/hf-shaders.iife.js (global `HFShaders`)
# from assets/driver/hf-shaders.js against the pinned npm `shaders` package. Builds in a temp dir so
# nothing lands on the shared volume except the one bundle. Default version = the pin in the source.
# After an upgrade: run check_determinism.mjs on a comp and material_grid.mjs on the materials you use.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
PIN="$(sed -n 's/^\/\/ pin: shaders@\([0-9.]*\).*/\1/p' "$HERE/assets/driver/hf-shaders.js" | head -1)"
VER="${1:-$PIN}"
[ -n "$VER" ] || { echo "no version given and no '// pin: shaders@x.y.z' line in hf-shaders.js" >&2; exit 2; }
B="$(mktemp -d /tmp/hfs-build.XXXXXX)"
trap 'rm -rf "$B"' EXIT
mkdir -p "$B/src"
cp "$HERE/assets/driver/hf-shaders.js" "$B/src/hf-shaders.js"
cd "$B"
npm init -y >/dev/null
npm i --no-audit --no-fund "shaders@$VER" esbuild@0.25.12 >/dev/null
npx esbuild src/hf-shaders.js --bundle --format=iife --global-name=HFShaders --minify --target=chrome120 \
  --legal-comments=eof --log-level=warning --outfile="$B/hf-shaders.iife.js"
if grep -qi '</script' "$B/hf-shaders.iife.js"; then echo "bundle contains </script: cannot be inlined" >&2; exit 1; fi
cp "$B/hf-shaders.iife.js" "$HERE/assets/driver/hf-shaders.iife.js"
if [ "$VER" != "$PIN" ]; then sed -i "s/^\/\/ pin: shaders@$PIN/\/\/ pin: shaders@$VER/" "$HERE/assets/driver/hf-shaders.js"; fi
echo "built shaders@$VER -> $HERE/assets/driver/hf-shaders.iife.js ($(wc -c < "$HERE/assets/driver/hf-shaders.iife.js") bytes, sha256 $(sha256sum "$HERE/assets/driver/hf-shaders.iife.js" | cut -c1-16))"
