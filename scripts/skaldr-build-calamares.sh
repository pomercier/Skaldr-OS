#!/usr/bin/env bash
# Rebuild official CachyOS Calamares against current Boost libraries.
# Temporary local package repository is used during ISO creation only.
set -euo pipefail

repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
work="$repo/.skaldr-calamares-build"
local_repo="$repo/.skaldr-local"
pkgbuild_revision="a7b305845d9f530db134d8a2cf94220e737beb9d"
# CachyOS force-pushes cachyos-staging: pinning a transient SHA here causes
# makepkg to fail with "unable to read tree" after upstream history rewrites.
# Resolve the source directly from the official live branch on EVERY build,
# then record/verify the exact commit that makepkg actually used. This makes
# the external source auditable while keeping the installer rebuild functional.
calamares_branch="cachyos-staging"
calamares_upstream="https://github.com/CachyOS/cachyos-calamares.git"

# Require exactly one installer package, matching the pinned local rebuild.
installer_packages="$(grep -E '^cachyos-calamares-' "$repo/archiso/packages_desktop.x86_64" || true)"
if [[ "$installer_packages" != "cachyos-calamares-staging" ]]; then
    echo "ISO Calamares package selection does not match the pinned staging rebuild" >&2
    exit 1
fi

command -v makepkg >/dev/null || { echo "makepkg is required" >&2; exit 1; }
command -v repo-add >/dev/null || { echo "repo-add (pacman-contrib) is required" >&2; exit 1; }
command -v git >/dev/null || { echo "git is required to verify Calamares source" >&2; exit 1; }
mkdir -p "$work" "$local_repo"
expected_revision=""
for attempt in 1 2 3; do
    expected_revision="$(git ls-remote --exit-code "$calamares_upstream" "refs/heads/$calamares_branch" | awk '{print $1}')" || :
    [[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] && break
    sleep "$((attempt * 5))"
done
[[ "$expected_revision" =~ ^[0-9a-f]{40}$ ]] || {
    echo "Could not resolve the official Calamares staging revision" >&2
    exit 1
}
echo "Official Calamares staging commit before build: $expected_revision"
curl --fail --location --silent --show-error --retry 3 \
  "https://raw.githubusercontent.com/CachyOS/CachyOS-PKGBUILDS/$pkgbuild_revision/cachyos-calamares-staging/PKGBUILD" \
  -o "$work/PKGBUILD"

grep -q '^pkgname=cachyos-calamares-staging$' "$work/PKGBUILD"
grep -q '^pkgrel=3$' "$work/PKGBUILD"
grep -q '#branch=cachyos-staging' "$work/PKGBUILD"
# Preserve official #branch= selection rather than using an obsolete commit
# hash after a CachyOS force-push; source identity is checked AFTER makepkg.
sed -i 's/^pkgrel=3$/pkgrel=3.1/' "$work/PKGBUILD"
# Fix unbalanced Qt reset notifications in the locally rebuilt installer.
# Only the extracted makepkg source is patched; upstream remains untouched.
cp -- "$repo/scripts/skaldr-patch-calamares-bootloader-model.py" "$work/skaldr-patch-calamares-bootloader-model.py"
python3 - "$work/PKGBUILD" <<'SKALDR_PREPARE_PATCH'
from pathlib import Path
import sys
path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
lines = [line for line in text.splitlines(keepends=True)
         if 'CALAMARES_VERSION_RC 1' in line and 'sed -i' in line]
if len(lines) != 1:
    raise SystemExit("Unexpected official Calamares PKGBUILD prepare(); refusing unreviewed patch")
dollar = chr(36)
injection = '    python3 "' + dollar + '{srcdir}/../skaldr-patch-calamares-bootloader-model.py" "' + dollar + '{srcdir}/calamares/src/modules/partition/core/BootLoaderModel.cpp"\n'
if injection in text or text.count(lines[0]) != 1:
    raise SystemExit("Calamares PKGBUILD prepare() already patched or changed")
path.write_text(text.replace(lines[0], lines[0] + injection), encoding="utf-8")
SKALDR_PREPARE_PATCH
echo "Building official CachyOS Calamares branch $calamares_branch against current Boost"

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
actual_revision="$(git -C "$work/src/calamares" rev-parse HEAD)"
[[ "$actual_revision" == "$expected_revision" ]] || {
    echo "Calamares source changed during build: expected $expected_revision, got $actual_revision" >&2
    exit 1
}
printf '%s\n' "$actual_revision" > "$local_repo/calamares-source.sha"
echo "PASS: exact Calamares source commit $actual_revision verified and recorded"
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
