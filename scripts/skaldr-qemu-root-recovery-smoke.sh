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
               ln grep find sort sed cat sfdisk mkfs.fat dd; do
    command -v "$program" >/dev/null 2>&1 || {
        echo "Missing CI dependency: $program" >&2
        exit 2
    }
done

workdir="$(mktemp -d "${RUNNER_TEMP%/}/skaldr-qemu-root-ci.XXXXXXXX")"
image="$workdir/disposable-root.img"
mnt="$workdir/mnt"
esp_mnt="$workdir/esp-mnt"
initrd="$workdir/initramfs.img"
config="$workdir/mkinitcpio.conf"
mkdir "$mnt" "$esp_mnt"
# Publish only QEMU serial logs; the disposable filesystem is always removed.
log_dir="${GITHUB_WORKSPACE:-$workdir}/results/qemu-root-recovery"
mkdir -p "$log_dir"

cleanup() {
    trap - EXIT
    if mountpoint -q "$esp_mnt"; then
        umount "$esp_mnt" || {
            echo "ERROR: scratch EFI filesystem still mounted; refusing deletion." >&2
            exit 1
        }
    fi
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

# GRUB is independently exercised as a BIOS rescue ISO (not installed into
# the test disk). The raw Btrfs image remains untouched by grub-mkrescue.
grub_iso_tree="$workdir/grub-cd"
mkdir -p "$grub_iso_tree/boot/grub"
cp -- "$kernel" "$grub_iso_tree/boot/vmlinuz-linux"
cp -- "$initrd" "$grub_iso_tree/boot/initramfs.img"

boot_grub_guest() {
    local description="$1" bootflags="$2" expected="$3" label="$4"
    local iso="$workdir/grub-$label.iso"
    local log="$log_dir/grub-$label.log"
    cat > "$grub_iso_tree/boot/grub/grub.cfg" <<GRUB_CONFIG
set default=0
set timeout=0
serial --unit=0 --speed=115200
terminal_input serial
terminal_output serial
menuentry 'Skaldr disposable Btrfs recovery root' {
    linux /boot/vmlinuz-linux console=ttyS0,115200 root=/dev/vda rootfstype=btrfs rw loglevel=4 $bootflags
    initrd /boot/initramfs.img
}
GRUB_CONFIG
    grub-mkrescue -o "$iso" "$grub_iso_tree" >/dev/null
    echo "Booting GRUB BIOS guest: $description"
    timeout -k 5s 120s qemu-system-x86_64 \
        -machine accel=tcg -cpu max -m 768M -smp 2 \
        -nodefaults -display none -monitor none -serial stdio -no-reboot \
        -boot d -cdrom "$iso" \
        -drive "file=$image,format=raw,if=virtio,cache=none" >"$log" 2>&1 || {
        echo "GRUB BIOS QEMU failed: $description" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    grep -Fq "SKALDR_QEMU_ROOT_STATE=$expected" "$log" || {
        echo "GRUB BIOS did not boot the selected Btrfs root: $description" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    echo "PASS: GRUB BIOS $description ($expected)"
}
boot_grub_guest "explicit rootflags" "rootflags=subvol=@" \
    "modified-after-snapshot" "explicit"
boot_grub_guest "restored default root" "" \
    "original-before-snapshot" "restored"

# Boot the same GRUB rescue ISOs through genuine UEFI firmware. Keep the
# packaged firmware code read-only and isolate NVRAM to this disposable VM.
boot_uefi_guest() {
    local label="$1" expected="$2"
    local iso="$workdir/grub-$label.iso"
    local log="$log_dir/uefi-grub-$label.log"
    local ovmf_code="/usr/share/edk2/x64/OVMF_CODE.4m.fd"
    local ovmf_template="/usr/share/edk2/x64/OVMF_VARS.4m.fd"
    local ovmf_vars="$workdir/ovmf-$label-vars.fd"
    [[ -f "$iso" && -f "$ovmf_code" && -f "$ovmf_template" ]] || {
        echo "UEFI rescue ISO or matching 4 MiB OVMF firmware missing." >&2
        exit 2
    }
    cp -- "$ovmf_template" "$ovmf_vars"
    echo "Booting disposable GRUB UEFI guest: $label"
    timeout -k 5s 150s qemu-system-x86_64 \
        -machine q35,accel=tcg -cpu max -m 1024M -smp 2 \
        -display none -monitor none -serial stdio -no-reboot \
        -drive "if=pflash,format=raw,readonly=on,file=$ovmf_code" \
        -drive "if=pflash,format=raw,file=$ovmf_vars" \
        -boot d -cdrom "$iso" \
        -drive "file=$image,format=raw,if=virtio,cache=none" >"$log" 2>&1 || {
        echo "UEFI GRUB QEMU boot failed: $label" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    grep -Fq "SKALDR_QEMU_ROOT_STATE=$expected" "$log" || {
        echo "UEFI GRUB boot did not reach expected Btrfs root: $label" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    echo "PASS: GRUB UEFI $label ($expected)"
}
boot_uefi_guest "explicit" "modified-after-snapshot"
boot_uefi_guest "restored" "original-before-snapshot"

# Limine v12 hybrid rescue ISOs are built from the distribution's official
# packaged binaries. These files exist ONLY in the newly allocated CI scratch
# directory; no host disk or installed bootloader is ever written.
boot_limine_case() {
    local label="$1" rootflags="$2" expected="$3"
    local iso_tree="$workdir/limine-$label"
    local iso="$workdir/limine-$label.iso"
    local source="/usr/share/limine"
    mkdir -p "$iso_tree/EFI/BOOT"
    for name in limine-uefi-cd.bin limine-bios-cd.bin limine-bios.sys BOOTX64.EFI; do
        [[ -f "$source/$name" ]] || {
            echo "Missing packaged Limine hybrid ISO file: $name" >&2
            exit 2
        }
    done
    cp -- "$source/limine-uefi-cd.bin" "$source/limine-bios-cd.bin" \
       "$source/limine-bios.sys" "$iso_tree/"
    cp -- "$source/BOOTX64.EFI" "$iso_tree/EFI/BOOT/BOOTX64.EFI"
    cp -- "$kernel" "$iso_tree/vmlinuz-linux"
    cp -- "$initrd" "$iso_tree/initramfs.img"
    cat > "$iso_tree/limine.conf" <<LIMINE_CONFIG
timeout: 0
serial: yes
/Skaldr disposable restored root
    protocol: linux
    path: boot():/vmlinuz-linux
    module_path: boot():/initramfs.img
    cmdline: console=ttyS0,115200 root=/dev/vda rootfstype=btrfs rw loglevel=4 $rootflags
LIMINE_CONFIG
    xorriso -as mkisofs -R -r -J -b limine-bios-cd.bin \
        -no-emul-boot -boot-load-size 4 -boot-info-table -hfsplus \
        -apm-block-size 2048 --efi-boot limine-uefi-cd.bin \
        -efi-boot-part --efi-boot-image --protective-msdos-label \
        "$iso_tree" -o "$iso" >/dev/null 2>&1 || {
        echo "Could not build disposable Limine rescue ISO: $label" >&2
        exit 1
    }
    # This writes ONLY the newly created, temporary Limine ISO.
    [[ "$iso" == "$workdir/limine-$label.iso" && -f "$iso" ]] || exit 2
    limine bios-install "$iso" >/dev/null

    local firmware log vars code="/usr/share/edk2/x64/OVMF_CODE.4m.fd"
    for firmware in bios uefi; do
        log="$log_dir/limine-$firmware-$label.log"
        echo "Booting disposable Limine $firmware root: $label"
        if [[ "$firmware" == "uefi" ]]; then
            vars="$workdir/limine-$label-vars.fd"
            cp -- /usr/share/edk2/x64/OVMF_VARS.4m.fd "$vars"
            timeout -k 5s 150s qemu-system-x86_64 \
                -machine q35,accel=tcg -cpu max -m 1024M -smp 2 \
                -display none -monitor none -serial stdio -no-reboot \
                -drive "if=pflash,format=raw,readonly=on,file=$code" \
                -drive "if=pflash,format=raw,file=$vars" \
                -boot d -cdrom "$iso" \
                -drive "file=$image,format=raw,if=virtio,cache=none" >"$log" 2>&1 || {
                echo "Limine UEFI guest failed for $label" >&2
                tail -n 80 "$log" >&2
                exit 1
            }
        else
            timeout -k 5s 120s qemu-system-x86_64 \
                -machine accel=tcg -cpu max -m 768M -smp 2 \
                -nodefaults -display none -monitor none -serial stdio -no-reboot \
                -boot d -cdrom "$iso" \
                -drive "file=$image,format=raw,if=virtio,cache=none" >"$log" 2>&1 || {
                echo "Limine BIOS guest failed for $label" >&2
                tail -n 80 "$log" >&2
                exit 1
            }
        fi
        grep -Fq "SKALDR_QEMU_ROOT_STATE=$expected" "$log" || {
            echo "Limine $firmware did not reach expected Btrfs root: $label" >&2
            tail -n 80 "$log" >&2
            exit 1
        }
        echo "PASS: Limine $firmware $label ($expected)"
    done
}
boot_limine_case "explicit" "rootflags=subvol=@" "modified-after-snapshot"
boot_limine_case "restored" "" "original-before-snapshot"

# Unlike the preceding rescue ISOs, this test places a Limine executable on
# an actual GPT EFI System Partition in a SECOND disposable disk image.
# The firmware boots the EFI fallback path from that disk with NO ISO attached.
# The original Btrfs image remains independent (second virtio device, /dev/vdb).
boot_limine_esp_disk="$workdir/limine-efi-boot.img"
esp_image="$workdir/limine-esp.img"
[[ ! -e "$boot_limine_esp_disk" && ! -e "$esp_image" ]] || exit 2
truncate -s 256M "$boot_limine_esp_disk"
# 128 MiB EFI System Partition at an exact 1 MiB offset. Explicit GPT type
# GUID avoids dependency on locale-specific sfdisk aliases.
sfdisk --no-reread "$boot_limine_esp_disk" >/dev/null <<'GPT_LAYOUT'
label: gpt
unit: sectors
start=2048,size=262144,type=c12a7328-f81f-11d2-ba4b-00a0c93ec93b
GPT_LAYOUT
truncate -s 128M "$esp_image"
mkfs.fat -F32 "$esp_image" >/dev/null

boot_installed_limine_case() {
    local label="$1" bootflags="$2" expected="$3"
    local vars="$workdir/esp-ovmf-$label-vars.fd"
    local log="$log_dir/limine-installed-efi-$label.log"
    local code="/usr/share/edk2/x64/OVMF_CODE.4m.fd"
    local template="/usr/share/edk2/x64/OVMF_VARS.4m.fd"
    mount -o loop "$esp_image" "$esp_mnt"
    mkdir -p "$esp_mnt/EFI/BOOT"
    cp -- /usr/share/limine/BOOTX64.EFI "$esp_mnt/EFI/BOOT/BOOTX64.EFI"
    cp -- "$kernel" "$esp_mnt/vmlinuz-linux"
    cp -- "$initrd" "$esp_mnt/initramfs.img"
    cat > "$esp_mnt/EFI/BOOT/limine.conf" <<LIMINE_CONFIG
timeout: 0
serial: yes
/Skaldr installed-disk recovery test
    protocol: linux
    path: boot():/vmlinuz-linux
    module_path: boot():/initramfs.img
    cmdline: console=ttyS0,115200 root=/dev/vdb rootfstype=btrfs rw loglevel=4 $bootflags
LIMINE_CONFIG
    umount "$esp_mnt"
    # Writes a preformatted 128 MiB FAT filesystem to the exact start of the
    # disposable GPT partition; never formats or mounts a host block device.
    dd if="$esp_image" of="$boot_limine_esp_disk" bs=1M seek=1 \
        conv=notrunc status=none
    cp -- "$template" "$vars"
    echo "Booting installed-disk Limine UEFI (no rescue ISO): $label"
    timeout -k 5s 150s qemu-system-x86_64 \
        -machine q35,accel=tcg -cpu max -m 1024M -smp 2 \
        -display none -monitor none -serial stdio -no-reboot \
        -drive "if=pflash,format=raw,readonly=on,file=$code" \
        -drive "if=pflash,format=raw,file=$vars" \
        -boot c \
        -drive "file=$boot_limine_esp_disk,format=raw,if=virtio,cache=none" \
        -drive "file=$image,format=raw,if=virtio,cache=none" >"$log" 2>&1 || {
        echo "Installed-disk Limine UEFI boot failed: $label" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    grep -Fq "SKALDR_QEMU_ROOT_STATE=$expected" "$log" || {
        echo "Installed-disk Limine selected the wrong Btrfs root: $label" >&2
        tail -n 80 "$log" >&2
        exit 1
    }
    echo "PASS: disk-backed Limine UEFI $label ($expected)"
}
boot_installed_limine_case "explicit" "rootflags=subvol=@" "modified-after-snapshot"
boot_installed_limine_case "restored" "" "original-before-snapshot"

# Confirm the same disk still contains both branches; never replace the source.
mount -o loop,subvolid=5 "$image" "$mnt"
[[ "$(cat "$mnt/@/etc/skaldr-ci-state")" == "modified-after-snapshot" ]] || exit 1
[[ "$(cat "$mnt/@restored/etc/skaldr-ci-state")" == "original-before-snapshot" ]] || exit 1
umount "$mnt"
echo "PASS: twelve QEMU boots including two disk-backed Limine UEFI boots, with both Btrfs roots verified."
echo "NOT TESTED: Calamares-installed KDE, its generated Limine entries, Secure Boot or physical recovery."
