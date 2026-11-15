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
6. Unmount the scratch filesystem before deleting the temporary image. A
   failed unmount prevents deletion; the disposable CI container is destroyed.

**Scope of this check:** Snapper setup, snapshot creation, read-only
verification and Btrfs data restoration. **Not proven:** the correctness of
an actual system-root rollback, bootloader entries, installed-drive recovery,
power-loss recovery or physical hardware. Those remain independent future
tests and must never be asserted from this scratch test alone.

This workflow does not publish an ISO, release, git tag or branch, and does
not modify the already validated five-job ISO build matrix.

[Snapper manual](https://man.archlinux.org/man/snapper.8) —
[ArchWiki Snapper](https://wiki.archlinux.org/title/Snapper).
