#!/usr/bin/env bash
# Construct an offline wallpaper from the approved raven logo at ISO build time.
set -euo pipefail
[[ $# -eq 1 ]] || { echo "Usage: skaldr-make-wallpaper AIROOTFS" >&2; exit 2; }
root="$1"
logo="$root/usr/share/pixmaps/skaldr-logo.png"
[[ -s "$logo" ]] || { echo "Skaldr logo missing: $logo" >&2; exit 1; }
destination="$root/usr/share/wallpapers/Skaldr/contents/images/1920x1080.svg"
mkdir -p "$(dirname "$destination")"
encoded="$(base64 -w 0 "$logo")"
cat > "$destination" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">
  <title>Skaldr OS — Nordic Raven</title>
  <defs>
    <radialGradient id="night" cx="51%" cy="42%" r="85%">
      <stop offset="0" stop-color="#18243c"/>
      <stop offset="0.55" stop-color="#0b1424"/>
      <stop offset="1" stop-color="#04070e"/>
    </radialGradient>
    <linearGradient id="aurora" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#00f0eb"/>
      <stop offset="0.49" stop-color="#336deb"/>
      <stop offset="1" stop-color="#d944f7"/>
    </linearGradient>
  </defs>
  <rect width="1920" height="1080" fill="url(#night)"/>
  <circle cx="960" cy="486" r="415" fill="none" stroke="url(#aurora)" stroke-width="1" opacity=".22"/>
  <circle cx="960" cy="486" r="327" fill="none" stroke="#6d97e8" stroke-width="1" opacity=".18"/>
  <path d="M-40 786 Q520 666 960 857 T1960 727" fill="none" stroke="url(#aurora)" stroke-width="2" opacity=".22"/>
  <path d="M-40 808 Q520 691 960 880 T1960 750" fill="none" stroke="#0ebfd0" stroke-width="1" opacity=".11"/>
  <image x="690" y="208" width="540" height="540" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,${encoded}"/>
  <text x="960" y="810" text-anchor="middle" fill="#d0d9e7" font-family="sans-serif" font-size="23" letter-spacing="7">PERFORMANCE BY INTENTION</text>
  <text x="960" y="850" text-anchor="middle" fill="#6c83a8" font-family="sans-serif" font-size="16" letter-spacing="4">FREEDOM BY DESIGN</text>
</svg>
SVG
echo "Created offline Skaldr OS wallpaper: $destination"
