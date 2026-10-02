#!/usr/bin/env bash
# tools/bootstrap.sh — idempotent. Rebuilds Muse's render + media toolchain inside the
# workspace (no root, no system packages). Safe to re-run any time; skips what exists.
#   Result: tools/env.sh  (source it: exports PATH, LD_LIBRARY_PATH, CHROME_PATH, PY)
# Pieces: headless Chrome (chrome-for-testing) + its shared libs extracted from Debian .debs,
#         static ffmpeg/ffprobe, a uv-managed Python venv (numpy scipy opencv pillow),
#         node deps for the studio (p5, p5.brush, puppeteer-core).
set -euo pipefail
T="$(cd "$(dirname "$0")" && pwd)"; W="$(dirname "$T")"
CHV="${CHROME_VERSION:-154.0.8037.57}"
log(){ echo "[bootstrap] $*"; }

# 1. Chrome headless shell
CH="$T/chrome/chrome-headless-shell-linux64/chrome-headless-shell"
if [ ! -x "$CH" ]; then
  log "chrome $CHV"; mkdir -p "$T/chrome"
  curl -sfL -o "$T/chrome/chs.zip" "https://storage.googleapis.com/chrome-for-testing-public/$CHV/linux64/chrome-headless-shell-linux64.zip"
  python3 -c "import zipfile,sys;zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])" "$T/chrome/chs.zip" "$T/chrome"
  rm -f "$T/chrome/chs.zip"; chmod +x "$CH"
fi

# 2. Shared libs Chrome needs (user-local apt state; dpkg-deb -x, no install)
L="$T/libs"
if [ ! -f "$L/.done" ]; then
  log "chrome libs"; A="$T/.apt"; mkdir -p "$A/state/lists/partial" "$A/cache/archives/partial" "$A/debs" "$L"
  O=(-o "Dir::State=$A/state" -o "Dir::Cache=$A/cache" -o Debug::NoLocking=1 -o "APT::Sandbox::User=$(whoami)")
  apt-get "${O[@]}" update >/dev/null
  PK="libglib2.0-0t64 libnspr4 libnss3 libatk1.0-0t64 libatk-bridge2.0-0t64 libdbus-1-3 libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 libxcb1 libxkbcommon0 libasound2t64 libatspi2.0-0t64 libxau6 libxdmcp6 libxrender1 libxi6 libdrm2 libwayland-server0 libexpat1 libffi8 libpcre2-8-0 libmount1 libselinux1 libblkid1 libsystemd0 libxshmfence1 libcairo2 libpango-1.0-0 libcups2t64 fonts-liberation fontconfig-config libfontconfig1 libfreetype6 libpng16-16t64 libbsd0 libmd0 libavahi-client3 libavahi-common3 libgnutls30t64 libxml2 libbrotli1 zlib1g libdrm-common libvulkan1 fonts-noto-color-emoji fonts-noto-core fonts-dejavu-core libzstd1 libcap2 libudev1 libatomic1"
  (cd "$A/debs" && for p in $PK; do apt-get "${O[@]}" download "$p" >/dev/null 2>&1 || echo "[bootstrap] WARN missing $p"; done)
  for f in "$A"/debs/*.deb; do dpkg-deb -x "$f" "$L"; done
  rm -rf "$A"; touch "$L/.done"
fi

# 3. ffmpeg (static, via npm ffmpeg-static) + ffprobe (static, via ffprobe-static)
if [ ! -x "$T/bin/ffmpeg" ]; then
  log "ffmpeg"; mkdir -p "$T/bin" "$T/ffmtmp"
  (cd "$T/ffmtmp" && npm init -y >/dev/null && npm i --silent ffmpeg-static ffprobe-static >/dev/null)
  cp "$T/ffmtmp/node_modules/ffmpeg-static/ffmpeg" "$T/bin/ffmpeg"
  cp "$(find "$T/ffmtmp/node_modules/ffprobe-static/bin/linux/x64" -name ffprobe)" "$T/bin/ffprobe"
  chmod +x "$T/bin/"*; rm -rf "$T/ffmtmp"
fi

# 4. Python venv via uv
if [ ! -x "$T/py/bin/python" ]; then
  log "python venv"; mkdir -p "$T/bin"
  if [ ! -x "$T/bin/uv" ]; then
    mkdir -p "$T/.uvtmp"
    curl -sfL https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-unknown-linux-gnu.tar.gz | tar xz -C "$T/.uvtmp"
    cp "$T"/.uvtmp/*/uv "$T/bin/uv"; rm -rf "$T/.uvtmp"
  fi
  "$T/bin/uv" venv -q "$T/py"
  VIRTUAL_ENV="$T/py" "$T/bin/uv" pip install -q numpy scipy pillow opencv-python-headless modal
fi

# 5. studio node deps
if [ -d "$W/studio" ] && [ ! -d "$W/studio/node_modules/p5.brush" ]; then
  log "studio node deps"; (cd "$W/studio" && npm i --ignore-scripts --silent >/dev/null)
fi

cat > "$T/env.sh" <<EOF
export PATH="$T/bin:\$PATH"
export LD_LIBRARY_PATH="$L/usr/lib/x86_64-linux-gnu:$L/lib/x86_64-linux-gnu\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"
export FONTCONFIG_PATH="$L/etc/fonts"
export CHROME_PATH="$CH"
export PY="$T/py/bin/python"
EOF
log "ok — source $T/env.sh"
