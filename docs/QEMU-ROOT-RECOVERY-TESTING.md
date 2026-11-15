# Skaldr OS — disposable Btrfs root boot verification

This is a **kernel-boot** test, not a complete distribution or bootloader
rollback certification. It runs on a temporary 768 MiB Btrfs image, inside
a disposable privileged GitHub Actions container, with QEMU software CPU
emulation (TCG). No host storage device or installed bootloader is modified.

The separate [workflow](../.github/workflows/skaldr-qemu-root-recovery.yml)
installs an ordinary Arch kernel, BusyBox, mkinitcpio and QEMU only in CI.
The test then:

1. Creates `@` and a read-only Btrfs `@snapshot` of its initial files.
2. Changes `@`, restores the snapshot to writable `@restored` and sets
   `@restored` as the default Btrfs subvolume.
3. Builds a real initramfs with Btrfs and virtio drivers.
4. Boots the Linux kernel in QEMU with `rootflags=subvol=@`. The **installed
   test root's** `/sbin/init` must print `modified-after-snapshot`, showing
   an explicit rootflags mount overrides the Btrfs default subvolume.
5. Powers off that guest; cold-boots the same disk without `rootflags`. Its
   `/sbin/init` must now print `original-before-snapshot`, showing the
   restored default subvolume was entered by an actual kernel and initramfs.
6. Builds a separate GRUB BIOS rescue ISO from the same CI kernel and initramfs,
   then boots that ISO twice: once with explicit `rootflags=subvol=@`, once
   using the restored Btrfs default. These are **real GRUB-to-kernel boot
   chains**, but GRUB is on a disposable ISO rather than installed to the disk.
7. Confirms the original and restored subvolumes are still separate and
   their contents are unchanged by the two boots.

Guest root state markers are produced only after the initramfs switches to
`/sbin/init` on the selected Btrfs root. Missing markers, boot timeout,
wrong state, or a nonzero QEMU exit fails the job. A pure source-level
mock or read-only mount check is not sufficient to pass this workflow.

**Still not tested:** an actual Calamares-installed Skaldr OS, its
Limine/GRUB/UEFI boot entries, complete installed KDE environment, kernel
upgrades, power-loss behavior or recovery on physical hardware. We must
verify all those independently before claiming full rollback support.

References: [Arch initramfs](https://wiki.archlinux.org/title/Arch_boot_process),
[mkinitcpio](https://wiki.archlinux.org/title/Mkinitcpio),
[BusyBox switch_root](https://github.com/mirror/busybox/blob/master/util-linux/switch_root.c).
