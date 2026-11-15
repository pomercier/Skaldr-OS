#!/usr/bin/env bash
# Bundle a pinned official ArtCraft Launcher AppImage for offline launch.
set -euo pipefail
[[ $# -eq 1 ]] || { echo "Usage: skaldr-stage-artcraft.sh AIROOTFS" >&2; exit 2; }
root="$1"
dest="$root/opt/skaldr/artcraft/artcraft-launcher.AppImage"
url="https://github.com/storytold/craft-launcher/releases/download/v0.19.2/artcraft-launcher-0.19.2-linux-x86_64.AppImage"
checksum="0218089916d60b4d288825d1542f13cb2ca5fb691418f4102201f43a84d1be7b"
mkdir -p "$(dirname "$dest")"
tmp="$dest.download"
trap 'rm -f "$tmp"' EXIT
curl --fail --location --show-error --silent --retry 4 --retry-delay 4 \
     --connect-timeout 25 "$url" --output "$tmp"
printf '%s  %s\n' "$checksum" "$tmp" | sha256sum --check --status || {
    echo "ArtCraft AppImage SHA-256 mismatch; refusing unverified file" >&2
    exit 1
}
install -m 0755 "$tmp" "$dest"
# Preserve the upstream Apache/MIT distribution licenses and attribution.
license_dir="$root/usr/share/licenses/skaldr-artcraft"
mkdir -p "$license_dir"
for filename in LICENSE-APACHE LICENSE-MIT NOTICE; do
    curl --fail --location --show-error --silent --retry 4 --retry-delay 4 \
         "https://raw.githubusercontent.com/storytold/craft-launcher/v0.19.2/$filename" \
         --output "$license_dir/$filename"
    test -s "$license_dir/$filename"
done
echo "Bundled verified ArtCraft Launcher v0.19.2 with licensing notices"

