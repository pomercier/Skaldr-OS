#!/usr/bin/env bash
# Rebuild official CachyOS Calamares against current Boost libraries.
# Temporary local package repository is used during ISO creation only.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
work="$repo/.skaldr-calamares-build"
local_repo="$repo/.skaldr-local"
pkgbuild_revision="a7b305845d9f530db134d8a2cf94220e737beb9d"
calamares_revision="42a91ab23334483ff3cd761d120dec9efea67c53"

# Verify the ISO package list selects the rebuilt installer, not a stale variant.
if [[ "$(grep -xc 'cachyos-calamares-staging' "$repo/archiso/packages_desktop.x86_64")" -ne 1 ]] ||
   grep -qx 'cachyos-calamares-next' "$repo/archiso/packages_desktop.x86_64"; then
    echo "ISO Calamares package selection does not match the pinned staging rebuild" >&2
    exit 1
fi

command -v makepkg >/dev/null || { echo "makepkg is required" >&2; exit 1; }
command -v repo-add >/dev/null || { echo "repo-add (pacman-contrib) is required" >&2; exit 1; }
mkdir -p "$work" "$local_repo"
curl --fail --location --silent --show-error --retry 3 \
  "https://raw.githubusercontent.com/CachyOS/CachyOS-PKGBUILDS/$pkgbuild_revision/cachyos-calamares-staging/PKGBUILD" \
  -o "$work/PKGBUILD"

grep -q '^pkgname=cachyos-calamares-staging$' "$work/PKGBUILD"
grep -q '^pkgrel=3$' "$work/PKGBUILD"
grep -q '#branch=cachyos-staging' "$work/PKGBUILD"
sed -i "s|#branch=cachyos-staging|#commit=$calamares_revision|" "$work/PKGBUILD"
sed -i 's/^pkgrel=3$/pkgrel=3.1/' "$work/PKGBUILD"
echo "Building official CachyOS Calamares source at $calamares_revision against current Boost"

# Build the installer for portable x86-64 regardless of the GitHub runner CPU.
# This prevents native-host optimizations from leaking into a distributable ISO.
# Preserve upstream hardening flags; the final -march/-mtune take precedence.
cp /etc/makepkg.conf "$work/skaldr-makepkg.conf"
cat >> "$work/skaldr-makepkg.conf" <<'MAKEPKG_PORTABLE'

# Skaldr OS: a rebuilt installer must not depend on the CI runner ISA.
CFLAGS+=" -march=x86-64 -mtune=generic"
CXXFLAGS+=" -march=x86-64 -mtune=generic"
MAKEPKG_PORTABLE

(
  cd "$work"
  export MAKEFLAGS="-j2"
  export CMAKE_BUILD_PARALLEL_LEVEL=2
  makepkg --config "$work/skaldr-makepkg.conf" --syncdeps --noconfirm --needed --cleanbuild
)
packages=("$work"/cachyos-calamares-staging-*.pkg.tar.zst)
[[ -f "${packages[0]}" ]] || { echo "No rebuilt Calamares package found" >&2; exit 1; }
cp -- "${packages[0]}" "$local_repo/"
repo-add "$local_repo/skaldr-local.db.tar.gz" "$local_repo/$(basename "${packages[0]}")"
[[ -e "$local_repo/skaldr-local.db" ]] || { echo "Local repository index is missing" >&2; exit 1; }

# Verify package's ELF contents, including dynamically linked C++ modules.
# Do not fake ABI compatibility by symlinking Boost 1.92 to Boost 1.91.
inspector="$work/abi-inspection"
mkdir -p "$inspector"
bsdtar -xf "${packages[0]}" -C "$inspector"
if grep -r -a -l 'libboost_python314.so.1.91.0' "$inspector/usr" >/dev/null; then
    echo "Rebuilt Calamares still references the obsolete Boost 1.91 ABI" >&2
    exit 1
fi
echo "Calamares local rebuild ready: $(basename "${packages[0]}")"
