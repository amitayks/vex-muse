#!/usr/bin/env bash
# Build one tesseract lab test into ../tesseract (one root composition per project dir, so tests share it in turn).
#   bash tesseract-src/build.sh turn|slice      (run from projects/lab-motion-tools)
set -euo pipefail
T="${1:?usage: build.sh turn|slice}"
cp ../../.pi/skills/svg-transform/assets/nd4.js tesseract/assets/js/nd4.js
python3 ../../.pi/skills/code-motion/scripts/hf_build.py "tesseract-src/$T.src.html" tesseract
