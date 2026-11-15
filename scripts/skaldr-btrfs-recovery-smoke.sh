#!/usr/bin/env bash
# Exercise Snapper and Btrfs in a disposable GitHub Actions container only.
set -Eeuo pipefail

if [[ "${GITHUB_ACTIONS:-}" != "true" ||
      "${SKALDR_BTRFS_CI_EXPLICIT:-}" != "disposable-ci-image" ]]; then
    echo "Refusing recovery test: dedicated ephemeral CI authorization is missing." >&2
    exit 2
fi
if [[ "$EUID" -ne 0 || -z "${RUNNER_TEMP:-}" || ! -d "$RUNNER_TEMP" ]]; then
    echo "Refusing recovery test: root in a valid CI temporary directory required." >&2
    exit 2
fi
for program in mktemp truncate mkfs.btrfs btrfs mount umount mountpoint \
               findmnt snapper cmp grep cat rm mkdir; do
    command -v "$program" >/dev/null 2>&1 || {
        echo "Missing CI dependency: $program" >&2
        exit 2
    }
done

workdir="$(mktemp -d "${RUNNER_TEMP%/}/skaldr-btrfs-ci.XXXXXXXX")"
image="$workdir/disposable.img"
mnt="$workdir/mnt"
config="skaldr-ci-$$"
config_created=0
root_changed=0
mkdir "$mnt"

cleanup() {
    trap - EXIT
    # On early failure, recover access to the original test subvolume and
    # Snapper configuration, even if the image default subvolume has changed.
    if [[ "$root_changed" -eq 1 ]]; then
        if mountpoint -q "$mnt"; then
            umount "$mnt" || { echo "Unable to unmount disposable test." >&2; exit 1; }
        fi
        if mount -o loop,subvolid=5 "$image" "$mnt"; then
            btrfs subvolume set-default 5 "$mnt" ||
                echo "Warning: scratch default subvolume could not be reset." >&2
        else
            echo "Warning: scratch top-level mount could not be restored." >&2
        fi
    fi
    if [[ "$config_created" -eq 1 ]]; then
        # Only the named configuration inside this disposable container.
        snapper --no-dbus -c "$config" delete-config >/dev/null 2>&1 ||
            echo "Warning: scratch Snapper configuration cleanup incomplete." >&2
    fi
    if mountpoint -q "$mnt"; then
        if ! umount "$mnt"; then
            echo "ERROR: scratch filesystem still mounted; refusing deletion." >&2
            exit 1
        fi
    fi
    if ! mountpoint -q "$mnt"; then
        rm -rf -- "$workdir"
    fi
}
trap cleanup EXIT

# mkfs.btrfs may target ONLY the temporary image allocated in this script.
[[ "$image" == "$workdir/disposable.img" && ! -e "$image" ]] || exit 2
truncate -s 512M "$image"
[[ -f "$image" && ! -L "$image" ]] || exit 2
mkfs.btrfs -f -m single -d single "$image" >/dev/null
mount -o loop "$image" "$mnt"
[[ "$(findmnt -n -o FSTYPE --target "$mnt")" == "btrfs" ]] || {
    echo "Scratch mount is not Btrfs." >&2
    exit 1
}

btrfs subvolume create "$mnt/@skaldr-test" >/dev/null
printf 'original-skaldr-ci-state\n' > "$mnt/@skaldr-test/state.txt"

# Native no-DBus mode matches the actual Skaldr installation process.
snapper --no-dbus -c "$config" create-config -f btrfs "$mnt/@skaldr-test"
config_created=1
snapper --no-dbus -c "$config" get-config >/dev/null
number="$(snapper --no-dbus -c "$config" create --type single \
          --description "Skaldr isolated recovery test" --print-number)"
[[ "$number" =~ ^[1-9][0-9]*$ ]] || {
    echo "Invalid snapshot identifier returned by Snapper." >&2
    exit 1
}
snapshot="$mnt/@skaldr-test/.snapshots/$number/snapshot"
[[ -d "$snapshot" && -f "$snapshot/state.txt" ]] || exit 1
[[ "$(cat "$snapshot/state.txt")" == "original-skaldr-ci-state" ]] || exit 1
btrfs property get -ts "$snapshot" ro | grep -qx 'ro=true'

printf 'modified-after-snapshot\n' > "$mnt/@skaldr-test/state.txt"
[[ "$(cat "$mnt/@skaldr-test/state.txt")" == "modified-after-snapshot" ]] || exit 1

# Restore a SEPARATE disposable subvolume; never replace the active root.
btrfs subvolume snapshot "$snapshot" "$mnt/@restored-test" >/dev/null
cmp -s "$snapshot/state.txt" "$mnt/@restored-test/state.txt"
[[ "$(cat "$mnt/@restored-test/state.txt")" == "original-skaldr-ci-state" ]] || {
    echo "Recovered content differs from its read-only snapshot." >&2
    exit 1
}
[[ "$(cat "$mnt/@skaldr-test/state.txt")" == "modified-after-snapshot" ]] || {
    echo "Recovery unexpectedly altered the original subvolume." >&2
    exit 1
}
# Test the root-selection semantics used by a boot path without
# pretending this checks a bootloader or installed KDE. This affects ONLY
# the newly created 512 MiB loopback image, never the host root.
restored_id="$(btrfs subvolume show "$mnt/@restored-test" |
               sed -n -E 's/^[[:space:]]*Subvolume ID:[[:space:]]*([0-9]+).*$/\1/p')"
[[ "$restored_id" =~ ^[1-9][0-9]*$ && "$restored_id" != "5" ]] || {
    echo "Cannot identify the restored scratch subvolume safely." >&2
    exit 1
}
btrfs subvolume set-default "$restored_id" "$mnt"
root_changed=1
umount "$mnt"
mount -o loop "$image" "$mnt"
[[ "$(cat "$mnt/state.txt")" == "original-skaldr-ci-state" ]] || {
    echo "Restored scratch root was not selected after remount." >&2
    exit 1
}
umount "$mnt"
# A kernel rootflags=subvol= mount overrides set-default. Demonstrate that
# blindly switching the default cannot recover such an installed boot path.
mount -o loop,subvol=@skaldr-test "$image" "$mnt"
[[ "$(cat "$mnt/state.txt")" == "modified-after-snapshot" ]] || {
    echo "Explicit subvol= unexpectedly followed the restored default root." >&2
    exit 1
}
umount "$mnt"
mount -o loop,subvolid=5 "$image" "$mnt"
[[ "$(cat "$mnt/@skaldr-test/state.txt")" == "modified-after-snapshot" ]] || {
    echo "Original scratch root unexpectedly changed during root selection." >&2
    exit 1
}
btrfs subvolume set-default 5 "$mnt"
root_changed=0
echo "PASS: Btrfs Snapper snapshot, independent recovery, default-root selection and explicit subvol override."
echo "NOT TESTED: real QEMU boot, installed-root rollback, KDE restart or bootloader integration."
