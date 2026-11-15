#!/usr/bin/env bash
# Prepare a restored COPY of a real Calamares-installed Quickemu Btrfs disk.
# This must never operate on a physical or user-provided disk.
set -Eeuo pipefail
if [[ "${GITHUB_ACTIONS:-}" != "true" ||
      "${SKALDR_CI_INSTALLED_ROLLBACK:-}" != "disposable-calamares-qcow2" ||
      "$EUID" -ne 0 || -z "${GITHUB_WORKSPACE:-}" ||
      -z "${RUNNER_TEMP:-}" || "$#" -ne 1 ]]; then
    echo "Refusing installed rollback: disposable CI authorization required." >&2
    exit 2
fi
disk="$1"
workspace="$(realpath -e "$GITHUB_WORKSPACE")"
expected="$workspace/machines/cachyos-dailylive/disk.qcow2"
[[ "$disk" == "$expected" && -f "$disk" && ! -L "$disk" &&
   -s "$disk" && "$workspace" != / ]] || {
    echo "Refusing rollback: expected a regular disposable Quickemu QCOW2." >&2
    exit 2
}
for cmd in qemu-img losetup sfdisk blkid mount umount mountpoint \
           btrfs realpath python3 mktemp mv sync; do
    command -v "$cmd" >/dev/null 2>&1 || {
        echo "Missing isolated recovery dependency: $cmd" >&2
        exit 2
    }
done
qemu-img info --output=json "$disk" | python3 -c '
import json, sys
record = json.load(sys.stdin)
assert record.get("format") == "qcow2"
assert 8 * 1024**3 <= record.get("virtual-size", 0) <= 64 * 1024**3
' || { echo "Unknown image format or virtual size; refusing." >&2; exit 2; }

scratch="$(mktemp -d "${RUNNER_TEMP%/}/skaldr-installed-root.XXXXXXXX")"
raw="$scratch/installed-raw.img"
restored="$scratch/recovered.qcow2"
top="$scratch/top"
mkdir "$top"
loopdev=""
cleanup() {
    trap - EXIT
    if mountpoint -q "$top"; then
        umount "$top" || { echo "Scratch root still mounted." >&2; exit 1; }
    fi
    if [[ -n "$loopdev" ]]; then
        losetup -d "$loopdev" || { echo "Scratch loop still attached." >&2; exit 1; }
    fi
    rm -rf -- "$scratch"
}
trap cleanup EXIT

echo "Preparing temporary copy of real Calamares-installed disk."
qemu-img convert -S 4k -O raw "$disk" "$raw"
[[ -f "$raw" && ! -L "$raw" ]] || exit 2
# Container runners may not create /dev/loopNpN partition nodes.
# Discover GPT boundaries in the scratch raw FILE, then probe each partition
# through its own size-limited loop mapping. Never touch real disks.
layout="$(sfdisk --json "$raw")" || {
    echo "Cannot inspect disposable GPT partition layout." >&2
    exit 1
}
# Parse the exact GPT bounds, then identify Btrfs by the documented
# primary on-disk superblock signature. Direct raw-file inspection avoids
# intermittent blkid/udev misses on size-limited loop mappings in CI.
# Mount below is still required to validate the filesystem and its integrity.
specs="$(python3 scripts/skaldr-find-btrfs-partition.py "$raw" <<< "$layout")" || {
    echo "Expected exactly one installed Btrfs partition; refusing rollback." >&2
    exit 1
}
read -r offset length <<< "$specs"
[[ "$offset" =~ ^[1-9][0-9]*$ && "$length" =~ ^[1-9][0-9]*$ ]] || {
    echo "Invalid recovered Btrfs partition geometry; refusing." >&2
    exit 1
}
loopdev="$(losetup --find --show --offset "$offset" --sizelimit "$length" "$raw")"
[[ -b "$loopdev" ]] || { echo "Disposable Btrfs loop device unavailable." >&2; exit 1; }
mount -t btrfs -o subvolid=5 "$loopdev" "$top"
root="$top/@"
[[ -d "$root/etc" && -d "$root/usr" ]] || {
    echo "Installed @ root not found; refusing guessed rollback." >&2
    exit 1
}
for name in @skaldr-ci-source-snapshot @skaldr-ci-changed @skaldr-ci-restored; do
    [[ ! -e "$top/$name" ]] || { echo "CI subvolume name collision." >&2; exit 1; }
done
# An installed bootloader pinned to an old numeric subvolume ID cannot
# be repaired by renaming @. Do not rewrite unknown bootloader configs.
if grep -RIEq 'rootflags=[^[:space:]]*subvolid=' \
       "$root/etc/default/limine" "$root/boot/limine.conf" \
       "$root/etc/kernel/cmdline" 2>/dev/null; then
    echo "Numeric Btrfs rootflags detected: refusing snapshot switch." >&2
    exit 1
fi

printf '%s\n' "original-before-rollback" > "$root/etc/skaldr-ci-rollback-state"
btrfs subvolume snapshot -r "$root" "$top/@skaldr-ci-source-snapshot" >/dev/null
printf '%s\n' "modified-after-snapshot" > "$root/etc/skaldr-ci-rollback-state"
btrfs subvolume snapshot "$top/@skaldr-ci-source-snapshot" \
    "$top/@skaldr-ci-restored" >/dev/null
mv "$root" "$top/@skaldr-ci-changed"
mv "$top/@skaldr-ci-restored" "$root"
id="$(btrfs subvolume show "$root" |
    sed -n -E 's/^[[:space:]]*Subvolume ID:[[:space:]]*([0-9]+).*$/\1/p')"
[[ "$id" =~ ^[1-9][0-9]*$ && "$id" != 5 ]] || exit 1
btrfs subvolume set-default "$id" "$top"
[[ "$(cat "$root/etc/skaldr-ci-rollback-state")" == "original-before-rollback" ]] || exit 1
[[ "$(cat "$top/@skaldr-ci-changed/etc/skaldr-ci-rollback-state")" == "modified-after-snapshot" ]] || exit 1
[[ "$(cat "$top/@skaldr-ci-source-snapshot/etc/skaldr-ci-rollback-state")" == "original-before-rollback" ]] || exit 1
btrfs property get -ts "$top/@skaldr-ci-source-snapshot" ro | grep -qx 'ro=true'
umount "$top"
losetup -d "$loopdev"
loopdev=""
qemu-img convert -S 4k -O qcow2 "$raw" "$restored"
qemu-img check "$restored" >/dev/null
[[ -s "$restored" && ! -L "$restored" ]] || exit 1
# Replace ONLY the CI VM file. Preserve the original until the replacement
# has succeeded; no physical block device or host bootloader is modified.
mv "$disk" "$scratch/unmodified-install.qcow2"
if ! mv "$restored" "$disk"; then
    mv "$scratch/unmodified-install.qcow2" "$disk"
    echo "Failed to stage the recovered CI disk." >&2
    exit 1
fi
echo "PASS: restored a disposable Btrfs root in a newly verified QCOW2 image."
echo "NOT YET VERIFIED: bootloader, KDE or VM reboot (tested by Quicktest next)."
