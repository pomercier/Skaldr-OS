# P0: virtual-machine installation interrupted by chwd

## Incident

A manual VM installation reported Calamares **"Failed to run chwd"**.
The installed disk did not boot afterward. That is an **incomplete
installation**, not an independently established bootloader defect.

CachyOS's Calamares chwd module runs:
\`\`\`text
arch-chroot <rootMountPoint> chwd --autoconfigure
\`\`\`
If chwd exits nonzero, Calamares fails before reaching later tasks such as
user creation and final bootloader configuration.

## Targeted corrective change

Commit \`048fc90039838cc9889fefbbfd1b33984439e5fa\` makes the live
Calamares configurator inspect PCI **display** controllers:

- Only known virtual-only QEMU/KVM, VMware, VirtualBox or Hyper-V graphics
  bypass this nonessential auto-configure step.
- The KDE online install manifest explicitly includes Mesa/software rendering
  and appropriate VM guest packages for that recognized profile.
- Unknown, physical, and passed-through GPU configurations retain the
  upstream chwd behavior. No driver is silently chosen on real hardware.
- The rest of Calamares's package, account, bootloader and filesystem
  stages remain mandatory.
- An unexpected chwd module layout is rejected, not silently ignored.

The added source-level regression suite covers PCI-based detection,
non-virtual fallback, exact Calamares step removal, guest packages, and
idempotent target configuration. **These tests alone do not certify the ISO.**

## Acceptance criteria

1. The source-level tests are green for the exact code.
2. The new ISO compiles successfully, with its own checksum/provenance.
3. On a new disposable VM disk, Calamares finishes **without** a chwd failure.
4. The virtual disk boots **with the ISO detached** for UEFI GRUB/ext4
   and UEFI Limine/Btrfs; KDE accepts a password and opens Control Center.
5. The recovery and ISO reconstruction jobs pass.
6. A manually tested VM outside QEMU remains a separate pending test.
   Results for VirtualBox or VMware must not be inferred from QEMU alone.

The old failed VM disk should be discarded or fully reinitialized for
retesting; it is not a valid install and should not be repaired in place
without a known-good snapshot or backup.

## Status tracking

The first build from the corrected installer source is GitHub Actions
[run 44400111821](https://github.com/pomercier/Skaldr-OS/actions/runs/44400111821).
A green result is required **from that exact run** before publishing the
new VM-focused preview.4 release. The [conditional preview.4 workflow]
(../.github/workflows/skaldr-vm-preview4.yml) only requests publication
if all five ISO and VM jobs are successful. The release workflow retains
its independent source and artifact checks.

The previously published preview.3 does **not** include the correction.
