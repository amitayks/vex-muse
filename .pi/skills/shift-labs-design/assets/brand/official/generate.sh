#!/bin/bash
# Generate Shift Labs keycap avatar PNGs in multiple color schemes.
# Requires: rsvg-convert (librsvg)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p svg png

colors=(
  "original        #F4B7BC #CB8E97 #1A2038"
  "midnight        #1A2038 #0F1424 #F4B7BC"
  "eggplant        #31263B #221A2A #F4B7BC"
  "ocean           #3B82F6 #2563EB #FFFFFF"
  "ocean-dark      #1E3A5F #152D4A #60A5FA"
  "emerald         #34D399 #10B981 #064E3B"
  "amber           #FBBF24 #F59E0B #78350F"
  "coral           #FB7185 #F43F5E #FFFFFF"
  "slate           #64748B #475569 #FFFFFF"
  "lavender        #A78BFA #8B5CF6 #FFFFFF"
  "mint            #6EE7B7 #34D399 #064E3B"
  "rose            #FDA4AF #FB7185 #881337"
  "white           #FFFFFF #E5E7EB #1A2038"
  "charcoal        #374151 #1F2937 #F9FAFB"
  "sky             #7DD3FC #38BDF8 #0C4A6E"
  "peach           #FDBA74 #FB923C #7C2D12"
)

for entry in "${colors[@]}"; do
  read -r name face shadow arrow <<< "$entry"

  cat > "svg/${name}.svg" << EOF
<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
  <rect width="512" height="512" fill="#FFFFFF"/>
  <g transform="translate(128, 96) scale(1.6)">
    <path d="m165.8 27.89c-3.52-4.67-7.19-6.18-13.6-6.18h-113.8c-9.45 0-16.59 8.52-16.59 17.22v110.2c0 10.5 6.43 18.04 16.91 18.04h111.1c10.48 0 16.96-7.46 16.96-17.13v-111.1c0-4.45 0.24-8.75-0.93-11.04z" fill="${shadow}"/>
    <path d="m150.8 21.71h-112.1c-9.35 0-16.47 8.46-16.47 17.09v96.34c0 10.97 7.2 18.05 16.69 18.05h109.9c10.05 0 16.6-7.53 16.6-17.69v-96.7c0-8.82-6.51-17.09-14.59-17.09z" fill="${face}"/>
    <path d="M64.38 97.93 94.38 62.94 124.38 97.93H108.38V117.42H80.38V97.93Z" fill="${arrow}" stroke="${arrow}" stroke-linejoin="miter" stroke-miterlimit="10" stroke-width="3"/>
  </g>
</svg>
EOF

  rsvg-convert -w 512 -h 512 "svg/${name}.svg" -o "png/${name}.png"
  echo "✓ ${name}"
done

echo ""
echo "Done — $(ls png/*.png | wc -l) PNGs in png/"
