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
mkdir "$mnt"

cleanup() {
    trap - EXIT
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
echo "PASS: Btrfs Snapper create, immutable snapshot, independent recovery copy."
echo "NOT TESTED: installed-root or bootloader rollback."
