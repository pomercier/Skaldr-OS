#!/usr/bin/env bash
# Rebuild official CachyOS Calamares against current Boost libraries.
# Temporary local package repository is used during ISO creation only.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
work="$repo/.skaldr-calamares-build"
local_repo="$repo/.skaldr-local"
pkgbuild_revision="288a24812b36c68bf16657e8131d00351878f3e0"
calamares_revision="199d71543db805fac2cc649ced72ad01dcb2c362"

command -v makepkg >/dev/null || { echo "makepkg is required" >&2; exit 1; }
command -v repo-add >/dev/null || { echo "repo-add (pacman-contrib) is required" >&2; exit 1; }
mkdir -p "$work" "$local_repo"
curl --fail --location --silent --show-error --retry 3 \
  "https://raw.githubusercontent.com/CachyOS/CachyOS-PKGBUILDS/$pkgbuild_revision/cachyos-calamares/PKGBUILD" \
  -o "$work/PKGBUILD"

grep -q '^pkgname=cachyos-calamares-next$' "$work/PKGBUILD"
grep -q '^pkgrel=13$' "$work/PKGBUILD"
grep -q '#branch=cachyos-dev' "$work/PKGBUILD"
sed -i "s|#branch=cachyos-dev|#commit=$calamares_revision|" "$work/PKGBUILD"
sed -i 's/^pkgrel=13$/pkgrel=13.1/' "$work/PKGBUILD"
echo "Building official CachyOS Calamares source at $calamares_revision against current Boost"

(
  cd "$work"
  export MAKEFLAGS="-j2"
  export CMAKE_BUILD_PARALLEL_LEVEL=2
  makepkg --syncdeps --noconfirm --needed --cleanbuild
)
packages=("$work"/cachyos-calamares-next-*.pkg.tar.zst)
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
