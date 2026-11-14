#!/usr/bin/env bash
# Fully scalable, offline Skaldr wallpapers. Never upscale the tiny icon PNG.
set -euo pipefail
[[ $# -eq 1 ]] || { echo "Usage: skaldr-make-wallpaper AIROOTFS" >&2; exit 2; }
root="$1"
dest="$root/usr/share/wallpapers/Skaldr/contents/images"
mkdir -p "$dest"
for spec in "3840 2160" "5120 2160"; do
    read -r width height <<< "$spec"
    center=$((width / 2))
    target="$dest/$width"x"$height.svg"
    cat > "$target" <<SVG
<svg xmlns="http://www.w3.org/2000/svg" width="$width" height="$height" viewBox="0 0 $width $height">
  <title>Skaldr OS — Nordic Raven, vector 4K</title>
  <defs>
    <radialGradient id="night"><stop stop-color="#1b2944"/><stop offset=".62" stop-color="#101b31"/><stop offset="1" stop-color="#060c1a"/></radialGradient>
    <linearGradient id="aurora"><stop stop-color="#02e8f3"/><stop offset=".48" stop-color="#276cef"/><stop offset="1" stop-color="#db36ec"/></linearGradient>
    <linearGradient id="metal"><stop stop-color="#f5fbff"/><stop offset=".47" stop-color="#a6bbd8"/><stop offset="1" stop-color="#f2fbff"/></linearGradient>
  </defs>
  <rect width="$width" height="$height" fill="url(#night)"/>
  <g transform="translate($center 920)">
    <circle r="850" fill="none" stroke="url(#aurora)" stroke-width="2" opacity=".23"/>
    <circle r="678" fill="none" stroke="#7898da" stroke-width="2" opacity=".18"/>
    <path d="M-680 80 Q-575 -520 0 -625 Q595 -520 685 80" fill="none" stroke="url(#aurora)" stroke-width="18" stroke-linecap="round"/>
    <path d="M-575 388 Q-285 750 72 700 Q420 662 570 400" fill="none" stroke="url(#aurora)" stroke-width="14" stroke-linecap="round"/>
    <g transform="translate(0 -210)">
      <!-- Original Skaldr visual language, redrawn as native SVG geometry. -->
      <path d="M-550 294 Q-405 175 -350 54 L-220 -48 Q-125 -264 94 -348 Q254 -355 339 -244 L436 -208 L365 -178 L510 -117 L357 -135 Q217 -101 209 45 L137 -12 L94 -91 L64 107 L-12 -45 L-116 203 L-151 75 L-369 350 L-248 107 Z" fill="#071425" stroke="#17334d" stroke-width="18"/>
      <path d="M-495 280 L-176 -50 Q-83 -211 92 -328 Q251 -350 337 -234 L465 -158 Q319 -187 251 -114 Q173 -33 181 62 L100 -67 L68 120 L-5 -66 L-96 201 L-158 65 L-357 310 L-245 87 Z" fill="url(#metal)" stroke="#f4fcff" stroke-width="10" stroke-linejoin="round"/>
      <path d="M-490 288 Q-287 74 -81 -47 Q-171 113 -260 176 L-352 307 Z" fill="#497493"/>
      <path d="M-422 336 L-108 95 L-218 244 L-314 369 Z" fill="#e6f5ff"/>
      <path d="M-243 291 Q-64 105 33 -65 L-10 104 L-114 287 Z" fill="#adcaea"/>
      <path d="M-55 -192 Q120 -333 283 -253 L363 -204 L262 -213 Q153 -250 46 -156 Z" fill="#f5fdff"/>
      <path d="M130 -152 Q270 -204 360 -161 L472 -141 L315 -106 L228 -42 Q236 -126 130 -152" fill="#051020"/>
      <path d="M168 -208 Q224 -247 285 -208 Q275 -171 223 -178 Z" fill="#00dffe" stroke="#e8ffff" stroke-width="9"/>
      <path d="M195 -196 L240 -201" stroke="#ffffff" stroke-width="10"/>
      <path d="M-127 -76 Q-39 -177 82 -208" fill="none" stroke="#0b2b46" stroke-width="21"/>
      <path d="M-223 30 Q-119 -80 16 -130" fill="none" stroke="#173b55" stroke-width="13"/>
    </g>
    <text x="0" y="550" font-family="DejaVu Sans,sans-serif" font-size="171" font-weight="900" letter-spacing="5" text-anchor="middle" fill="url(#metal)">SKALDR OS</text>
    <path d="M-320 615 H-82 M82 615 H320" stroke="url(#aurora)" stroke-width="13" stroke-linecap="round"/>
    <path d="M0 580 L70 711 H-70 Z M0 620 L35 693 H-35 Z" stroke="#bcdaf0" stroke-width="9" fill="#101b30"/>
  </g>
  <path d="M0 1735 Q$center 1950 $width 1735" fill="none" stroke="url(#aurora)" stroke-width="4" opacity=".37"/>
  <text x="$center" y="1855" text-anchor="middle" fill="#c6d5e9" font-size="55" font-family="DejaVu Sans,sans-serif" letter-spacing="10">PERFORMANCE BY INTENTION</text>
  <text x="$center" y="1960" text-anchor="middle" fill="#7890b1" font-size="35" font-family="DejaVu Sans,sans-serif" letter-spacing="8">FREEDOM BY DESIGN</text>
</svg>
SVG
    echo "Created pixel-independent Skaldr wallpaper: $target"
done
