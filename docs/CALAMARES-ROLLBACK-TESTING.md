# Calamares-installed Btrfs rollback: real VM integration

This is the next validation after the isolated 12/12 QEMU kernel and
bootloader smoke tests. The separate smoke tests use a minimal root; this
test exercises the **actual installed Skaldr OS**, installed by Calamares.

The full Desktop ISO Quicktest Limine/Btrfs matrix job:

1. Installs Skaldr through Calamares into a 48 GiB sparse Quickemu QCOW2
   disk using the usual GUI and real package installation.
2. Cold-boots the installed system **with no ISO**, logs in with the
   password-protected CI account and opens the native Skaldr Control Center.
3. Powers off QEMU, then calls the CI-only offline rollback helper. It
   refuses all targets other than the fixed disposable Quickemu QCOW2 path.
4. Converts the VM disk to a **separate temporary raw image**, mounts only
   its Btrfs partition with a loop device and locates the Calamares-created
   `@` root subvolume; unexpected layouts fail rather than being guessed.
5. Creates a read-only root snapshot with a pre-change marker, changes the
   working `@` marker, and creates a separate writable restored snapshot.
6. Retains the original changed `@` under a different name, renames the
   restored root into `@`, and changes the disposable image's Btrfs default.
   A hardcoded numeric `rootflags=subvolid=` detected in the installed
   files causes a fail-closed refusal; existing boot files aren't rewritten.
7. Converts the verified raw disk back to a *new* QCOW2 and replaces the
   disposable Quickemu disk only after validation, keeping the original
   safely isolated during conversion.
8. Boots **without the installation ISO**, verifies KDE's real login
   greeter, authenticates, opens Konsole and reads
   `/etc/skaldr-ci-rollback-state` from inside the guest.
9. Requires the restored original marker and launches the Skaldr Control
   Center, requiring a populated system overview and kernel field.

This is a test for a manually prepared rollback on a temporary CI image,
**not** an automatic end-user rollback feature. It does not certify
unexpected storage layouts, different bootloaders, Secure Boot, encrypted
root partitions, physical hardware or power-loss recovery. No user's
real disk, partition table, or bootloader is modified.

The test is gated on `TEST_BOOTLOADER=limine` and
`TEST_FILESYSTEM=btrfs`; other ISO matrix jobs are unchanged.
Never mark this check complete until its **five-job Desktop ISO workflow**
passes and its Limine/Btrfs job includes the guest marker/KDE assertions.

## Independent synthetic-image rehearsal

A separate, inexpensive CI job runs
`scripts/skaldr-installed-rollback-image-smoke.sh`. It creates a sparse
8 GiB GPT disk **file** with a real 1 GiB Btrfs partition and `@` root,
converts the disk to a disposable QCOW2, and runs the **same offline helper**
used by the full Calamares test. It reopens the restored QCOW2 through a
loop device to verify the restored root, the preserved modified root,
the default Btrfs subvolume and the immutable source snapshot.

This validates real `qemu-img`, GPT, loop mounting and Btrfs filesystem
operations without requiring a multi-gigabyte ISO. It is intentionally
not an installation or kernel boot test. The full installed KDE/Calamares
scenario remains mandatory and separately gated.

## Partition discovery in isolated containers

GitHub's privileged runner may expose `/dev/loopN` but not
`/dev/loopNpN` partition nodes. The helper reads the GPT geometry from the
**temporary raw disk file**, creates a size-bounded loop mapping for each
partition using `losetup --offset --sizelimit`, and detects the unique Btrfs
filesystem. The synthetic test uses the same method with its known GPT
partition offset. No physical disk is opened or formatted.

## Explicit numeric-rootflags refusal

The synthetic image workflow additionally creates a temporary boot config
with `rootflags=subvolid=256`. It requires the rollback helper to refuse
the operation for that specific reason and verifies the original QCOW2
retains its exact SHA-256 digest. After removing that intentionally unsafe
option from the **synthetic fixture**, the workflow must then complete the
normal rollback. This negative test is separate from KDE boot validation.

## Independent integration probe using validated ISO 87

The separate
[`skaldr-installed-rollback-probe.yml`](../.github/workflows/skaldr-installed-rollback-probe.yml)
workflow runs **the new current CI rollback code** against a previously
validated and independently checksum-verified ISO from Desktop ISO run
`43745598535`. That older ISO already passed Calamares installation,
Limine/Btrfs cold reboot and KDE login. The probe reuses it to avoid waiting
for a full new image build before diagnosing the newly added rollback stage.

This is an *integration debugging probe*, not proof that the ISO built from
the latest source commit passes. Release authorization continues to require
successful source and full Desktop ISO workflows for the exact same revision.
