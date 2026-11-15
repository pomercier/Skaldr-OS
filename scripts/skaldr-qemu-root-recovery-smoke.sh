#!/usr/bin/env bash
# Boot an actual Linux kernel twice against one disposable Btrfs image.
# NEVER target installed devices, the CI runner root, or a host bootloader.
set -Eeuo pipefail

if [[ "${GITHUB_ACTIONS:-}" != "true" ||
      "${SKALDR_QEMU_CI_EXPLICIT:-}" != "disposable-qemu-root-image" ||
      "$EUID" -ne 0 || -z "${RUNNER_TEMP:-}" || ! -d "$RUNNER_TEMP" ]]; then
    echo "Refusing QEMU recovery test: disposable CI authorization required." >&2
    exit 2
fi
for program in mktemp truncate mkfs.btrfs btrfs mount umount mountpoint \
               mkinitcpio qemu-system-x86_64 timeout ldd awk cp install \
               ln grep find sort sed cat; do
    command -v "$program" >/dev/null 2>&1 || {
        echo "Missing CI dependency: $program" >&2
        exit 2
    }
done

workdir="$(mktemp -d "${RUNNER_TEMP%/}/skaldr-qemu-root-ci.XXXXXXXX")"
image="$workdir/disposable-root.img"
mnt="$workdir/mnt"
initrd="$workdir/initramfs.img"
config="$workdir/mkinitcpio.conf"
mkdir "$mnt"
# Publish only QEMU serial logs; the disposable filesystem is always removed.
log_dir="${GITHUB_WORKSPACE:-$workdir}/results/qemu-root-recovery"
mkdir -p "$log_dir"

cleanup() {
    trap - EXIT
    if mountpoint -q "$mnt"; then
        umount "$mnt" || {
            echo "ERROR: scratch Btrfs still mounted; refusing deletion." >&2
            exit 1
        }
    fi
    rm -rf -- "$workdir"
}
trap cleanup EXIT

# A newly allocated ordinary file is the ONLY target of mkfs.btrfs.
[[ "$image" == "$workdir/disposable-root.img" && ! -e "$image" ]] || exit 2
truncate -s 768M "$image"
[[ -f "$image" && ! -L "$image" ]] || exit 2
mkfs.btrfs -f -m single -d single "$image" >/dev/null
mount -o loop "$image" "$mnt"
btrfs subvolume create "$mnt/@" >/dev/null
root="$mnt/@"
mkdir -p "$root"/{bin,sbin,etc,dev,proc,sys}

# Put an actual /sbin/init and its shell on the Btrfs root, not in the
# initramfs. A successful boot marker therefore proves switch_root occurred.
busybox="$(command -v busybox)"
install -m 0755 "$busybox" "$root/bin/busybox"
ln -s busybox "$root/bin/sh"
# BusyBox can be dynamically linked on Arch. Copy all direct ldd libraries,
# including the ELF interpreter, into this disposable guest root only.
while IFS= read -r library; do
    [[ -f "$library" ]] || { echo "Missing BusyBox runtime library: $library" >&2; exit 1; }
    mkdir -p "$root$(dirname "$library")"
    cp -L -- "$library" "$root$library"
done < <(ldd "$busybox" | awk '{ for (i=1; i<=NF; i++) if ($i ~ /^\//) print $i }' | sort -u)
cat > "$root/sbin/init" <<'GUEST_INIT'
#!/bin/sh
exec </dev/console >/dev/console 2>&1
state="$(/bin/busybox cat /etc/skaldr-ci-state 2>/dev/null)"
case "$state" in
    modified-after-snapshot|original-before-snapshot)
        printf 'SKALDR_QEMU_ROOT_STATE=%s\n' "$state" ;;
    *)
        echo 'SKALDR_QEMU_ROOT_STATE=INVALID'
        /bin/busybox poweroff -f
        exit 1 ;;
esac
/bin/busybox sync
/bin/busybox poweroff -f
GUEST_INIT
chmod 0755 "$root/sbin/init"
printf 'original-before-snapshot\n' > "$root/etc/skaldr-ci-state"
btrfs subvolume snapshot -r "$root" "$mnt/@snapshot" >/dev/null
printf 'modified-after-snapshot\n' > "$root/etc/skaldr-ci-state"
btrfs subvolume snapshot "$mnt/@snapshot" "$mnt/@restored" >/dev/null
[[ "$(cat "$mnt/@restored/etc/skaldr-ci-state")" == "original-before-snapshot" ]] || exit 1
[[ "$(cat "$root/etc/skaldr-ci-state")" == "modified-after-snapshot" ]] || exit 1
restored_id="$(btrfs subvolume show "$mnt/@restored" |
               sed -n -E 's/^[[:space:]]*Subvolume ID:[[:space:]]*([0-9]+).*$/\1/p')"
[[ "$restored_id" =~ ^[1-9][0-9]*$ && "$restored_id" != "5" ]] || exit 1
btrfs subvolume set-default "$restored_id" "$mnt"
umount "$mnt"

kernel="$(find /usr/lib/modules -mindepth 2 -maxdepth 2 -name vmlinuz -type f -print -quit)"
[[ -n "$kernel" && -f "$kernel" ]] || {
    echo "An installed Arch Linux kernel image is required in the CI container." >&2
    exit 1
}
kver="$(basename "$(dirname "$kernel")")"
cat > "$config" <<'MKINITCPIO'
MODULES=(virtio_pci virtio_blk btrfs)
BINARIES=()
FILES=()
HOOKS=(base udev block filesystems)
COMPRESSION="gzip"
MKINITCPIO
mkinitcpio --kernel "$kver" --config "$config" --generate "$initrd" --nopost
[[ -s "$initrd" ]] || exit 1

boot_guest() {
    local description="$1" bootflags="$2" expected="$3" log="$4"
    echo "Booting disposable QEMU guest: $description"
    timeout -k 5s 120s qemu-system-x86_64 \
        -machine accel=tcg -cpu max -m 768M -smp 2 \
        -nodefaults -display none -monitor none -serial stdio -no-reboot \
        -kernel "$kernel" -initrd "$initrd" \
        -append "console=ttyS0,115200 root=/dev/vda rootfstype=btrfs rw loglevel=4 $bootflags" \
        -drive "file=$image,format=raw,if=virtio,cache=none" >"$log" 2>&1 || {
        echo "QEMU failed to complete $description; last guest log lines:" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    grep -Fq "SKALDR_QEMU_ROOT_STATE=$expected" "$log" || {
        echo "QEMU boot did not reach expected Btrfs root for $description." >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    echo "PASS: $description ($expected)"
}

# First cold boot overrides the default Btrfs root and enters modified @.
boot_guest "explicit original rootflags" "rootflags=subvol=@" \
    "modified-after-snapshot" "$log_dir/explicit-root.log"
# Second cold boot omits rootflags and must enter the recovered default root.
boot_guest "restored default root" "" \
    "original-before-snapshot" "$log_dir/restored-root.log"

# Confirm the same disk still contains both branches; never replace the source.
mount -o loop,subvolid=5 "$image" "$mnt"
[[ "$(cat "$mnt/@/etc/skaldr-ci-state")" == "modified-after-snapshot" ]] || exit 1
[[ "$(cat "$mnt/@restored/etc/skaldr-ci-state")" == "original-before-snapshot" ]] || exit 1
umount "$mnt"
echo "PASS: two real QEMU kernel boots, explicit Btrfs subvol override, restored default root and switch_root."
echo "NOT TESTED: full Skaldr installed KDE, UEFI/GRUB/Limine entries or physical recovery."
