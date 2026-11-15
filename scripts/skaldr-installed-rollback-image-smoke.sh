#!/usr/bin/env bash
# Fast real-filesystem rehearsal for the CI-only installed-disk rollback helper.
# This creates a NEW synthetic QCOW2 in the permitted Quickemu CI path.
set -Eeuo pipefail
if [[ "${GITHUB_ACTIONS:-}" != "true" ||
      "${SKALDR_CI_INSTALLED_ROLLBACK:-}" != "disposable-calamares-qcow2" ||
      "$EUID" -ne 0 || -z "${GITHUB_WORKSPACE:-}" ||
      -z "${RUNNER_TEMP:-}" ]]; then
    echo "Refusing image rehearsal outside authorized disposable CI." >&2
    exit 2
fi
scratch="$(mktemp -d "${RUNNER_TEMP%/}/skaldr-rollback-smoke.XXXXXXXX")"
raw="$scratch/source.img"
verified_raw="$scratch/recovered.img"
mountpoint_dir="$scratch/top"
loopdev=""
disk="$GITHUB_WORKSPACE/machines/cachyos-dailylive/disk.qcow2"
mkdir -p "$mountpoint_dir" "$(dirname "$disk")"
[[ ! -e "$disk" && ! -L "$disk" ]] || {
    echo "CI synthetic disk destination already exists; refusing overwrite." >&2
    exit 2
}
cleanup() {
    trap - EXIT
    if mountpoint -q "$mountpoint_dir"; then umount "$mountpoint_dir"; fi
    if [[ -n "$loopdev" ]]; then losetup -d "$loopdev"; fi
    rm -f -- "$disk"
    rm -rf -- "$scratch"
}
trap cleanup EXIT
truncate -s 8G "$raw"
sfdisk "$raw" >/dev/null <<'GPT_PARTITIONS'
label: gpt
unit: sectors
start=2048,size=262144,type=c12a7328-f81f-11d2-ba4b-00a0c93ec93b
start=264192,size=2097152,type=0fc63daf-8483-4772-8e79-3d69d8477de4
GPT_PARTITIONS
# No /dev/loopNp2 nodes are needed: this is an offset-mapped partition of
# the newly generated scratch raw file, never a physical disk.
loopdev="$(losetup --find --show --offset "$((264192 * 512))" \
    --sizelimit "$((2097152 * 512))" "$raw")"
mkfs.btrfs -f -m single -d single "$loopdev" >/dev/null
mount "$loopdev" "$mountpoint_dir"
btrfs subvolume create "$mountpoint_dir/@" >/dev/null
mkdir -p "$mountpoint_dir/@/etc/default" "$mountpoint_dir/@/usr"
printf 'synthetic-calamares-fixture\n' > "$mountpoint_dir/@/etc/skaldr-ci-fixture"
printf 'KERNEL_CMDLINE[default]="rootflags=subvolid=256"\n' > "$mountpoint_dir/@/etc/default/limine"
umount "$mountpoint_dir"
losetup -d "$loopdev"
loopdev=""
qemu-img convert -S 4k -O qcow2 "$raw" "$disk"
qemu-img check "$disk" >/dev/null
# A hard-coded numeric root ID must be refused WITHOUT modifying the source
# QCOW2, because moving @ cannot redirect a bootloader pinned to that ID.
before="$(sha256sum "$disk" | cut -d' ' -f1)"
if bash scripts/skaldr-ci-installed-rollback.sh "$disk" > "$scratch/refusal.log" 2>&1; then
    echo "Unsafe numeric Btrfs rootflags were unexpectedly accepted." >&2
    exit 1
fi
grep -Fq "Numeric Btrfs rootflags detected" "$scratch/refusal.log" || {
    echo "Rollback refused, but for the wrong reason." >&2
    cat "$scratch/refusal.log" >&2
    exit 1
}
after="$(sha256sum "$disk" | cut -d' ' -f1)"
[[ "$before" == "$after" ]] || {
    echo "Rejected rollback unexpectedly changed the original QCOW2." >&2
    exit 1
}
echo "PASS: pinned numeric Btrfs rootflags refused with unchanged QCOW2."

# Remove the deliberately unsafe selector from the private synthetic RAW
# fixture; the same helper must now succeed on a valid supported layout.
loopdev="$(losetup --find --show --offset "$((264192 * 512))" \
    --sizelimit "$((2097152 * 512))" "$raw")"
mount "$loopdev" "$mountpoint_dir"
rm -- "$mountpoint_dir/@/etc/default/limine"
umount "$mountpoint_dir"
losetup -d "$loopdev"
loopdev=""
rm -f -- "$disk"
qemu-img convert -S 4k -O qcow2 "$raw" "$disk"
qemu-img check "$disk" >/dev/null
bash scripts/skaldr-ci-installed-rollback.sh "$disk"

# Verify the resulting root was restored, the modified root was retained,
# and the read-only source snapshot still contains the original marker.
qemu-img convert -S 4k -O raw "$disk" "$verified_raw"
loopdev="$(losetup --find --show --offset "$((264192 * 512))" \
    --sizelimit "$((2097152 * 512))" "$verified_raw")"
mount -t btrfs -o subvolid=5 "$loopdev" "$mountpoint_dir"
[[ "$(cat "$mountpoint_dir/@/etc/skaldr-ci-rollback-state")" == "original-before-rollback" ]]
[[ "$(cat "$mountpoint_dir/@skaldr-ci-changed/etc/skaldr-ci-rollback-state")" == "modified-after-snapshot" ]]
[[ "$(cat "$mountpoint_dir/@skaldr-ci-source-snapshot/etc/skaldr-ci-rollback-state")" == "original-before-rollback" ]]
[[ "$(cat "$mountpoint_dir/@/etc/skaldr-ci-fixture")" == "synthetic-calamares-fixture" ]]
btrfs property get -ts "$mountpoint_dir/@skaldr-ci-source-snapshot" ro | grep -qx 'ro=true'
default_id="$(btrfs subvolume get-default "$mountpoint_dir" |
    sed -n -E 's/^ID ([0-9]+) .*/\1/p')"
root_id="$(btrfs subvolume show "$mountpoint_dir/@" |
    sed -n -E 's/^[[:space:]]*Subvolume ID:[[:space:]]*([0-9]+).*$/\1/p')"
[[ -n "$root_id" && "$default_id" == "$root_id" ]]
umount "$mountpoint_dir"
losetup -d "$loopdev"
loopdev=""
echo "PASS: synthetic GPT/Btrfs QCOW2 restored with original and changed roots, correct default and immutable snapshot."
echo "NOT TESTED: installed Calamares, actual Limine boot, KDE or hardware."
