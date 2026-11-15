# Skaldr OS — disposable Btrfs recovery smoke test

The separate [Btrfs recovery smoke](../.github/workflows/skaldr-btrfs-recovery.yml)
workflow exercises a **real Btrfs filesystem** created inside a private,
temporary 512 MiB image in a disposable, privileged CI container. This
test neither operates on the runner's physical disks nor restores an installed
system's root volume.

It validates the following sequence:

1. Refuse execution unless GitHub Actions, root privileges and a dedicated
   `SKALDR_BTRFS_CI_EXPLICIT=disposable-ci-image` acknowledgement are present.
2. Format an ordinary file generated inside a newly allocated temporary
   directory, then mount it with the loop device.
3. Create an isolated Btrfs subvolume and an independent Snapper configuration,
   using the same `--no-dbus` mode employed during installation.
4. Create a real read-only Snapper snapshot and verify its original file contents.
5. Modify the active scratch subvolume, create a **separate** writable
   restored subvolume from the snapshot and verify that original data is
   recovered without changing the modified live scratch subvolume.
6. Select the restored Btrfs subvolume as the **default** root of the same
   disposable image; unmount and remount it without a `subvol=` override to
   confirm that the recovered file is now visible at the mount root.
7. Mount explicitly with `subvol=@skaldr-test` and prove this deliberately
   selects the original, modified root **despite** the restored default. A
   kernel `rootflags=subvol=` or `rootflags=subvolid=` can therefore prevent
   a default-subvolume switch from changing the actual boot root.
8. Remount the Btrfs top-level (`subvolid=5`), confirm the original modified
   subvolume is untouched, and restore the default subvolume to ID 5.
9. Unmount the scratch filesystem before deleting the temporary image. A
   failed unmount prevents deletion; the disposable CI container is destroyed.

**Scope of this check:** Snapper setup, snapshot creation, read-only
verification, Btrfs data restoration, default-root selection after remount,
and the precedence of an explicit subvolume mount option.
**Not proven:** the correctness of
an actual system-root rollback, bootloader entries, installed-drive recovery,
power-loss recovery or physical hardware. Those remain independent future
tests and must never be asserted from this scratch test alone.

This workflow does not publish an ISO, release, git tag or branch, and does
not modify the already validated five-job ISO build matrix.

[Snapper manual](https://man.archlinux.org/man/snapper.8) —
[ArchWiki Snapper](https://wiki.archlinux.org/title/Snapper).

## Read-only installed-system diagnostics

Run `skaldr-recovery` on an installed system to inspect the **current**
kernel command line without modifying snapshots or bootloader files.
`kernel_root_subvolume_override` reports an explicit `rootflags=subvol=`
or `rootflags=subvolid=` option when present.
`default_subvolume_change_sufficient_for_boot` is `false` when an
override is detected, and otherwise **unknown**, never a claim of safety.

The current command line is not proof of every available recovery boot entry.
Before claiming real rollback, a separate disposable VM must verify the
installed bootloader and initramfs, any explicit rootflags, `/etc/fstab`,
restoring a writable root snapshot, an ISO-detached restart and KDE login.

References: [Btrfs mount options](https://btrfs.readthedocs.io/en/stable/btrfs-man5.html),
[ArchWiki Btrfs](https://wiki.archlinux.org/title/Btrfs).
