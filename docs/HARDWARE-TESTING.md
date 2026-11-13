# Skaldr OS — physical hardware validation

The [first public preview](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1)
is **not certified for production systems**. The exact ISO passed all
[five virtual-machine CI jobs](https://github.com/pomercier/Skaldr-OS/actions/runs/43507233020)
and the source test suite for commit `b391fc35f4eaade3c1ff5231c33c10f63770bda6`.

## Before installing

- [ ] Use a spare computer or disposable test SSD, **not the only system drive**.
- [ ] Verify independent data backups and keep a bootable rescue medium.
- [ ] Download all seven GitHub Release files and reassemble with Python 3,
      verifying each part and the complete ISO.
- [ ] Confirm the exact `skaldr-0.1.0-dev.62-x86_64.iso` checksum:

```text
b553c0e4cfe01e1de0c857f1dc4c70ac89d41a762bdb01750c770bb77069ec49
```

- [ ] Record CPU, RAM, GPU model/vendor, storage, firmware UEFI/BIOS mode and
      Secure Boot state before testing.

## Installation and boot

- [ ] Boot the live ISO, open the installer and explicitly verify the target drive.
- [ ] Install **GRUB/ext4** onto a disposable drive; cold boot without the ISO.
- [ ] Separately install **Limine/Btrfs**; cold boot without the ISO.
- [ ] Confirm account password is required and KDE Plasma launches.
- [ ] Confirm Skaldr welcome, NumLock at login/resume, network and audio.
- [ ] Validate legacy BIOS **installation** separately; only BIOS *live boot*
      was demonstrated by CI.
- [ ] Test actual recovery boot entries without `mitigations=off` when provided.

## Vendor-neutral GPU coverage

| Hardware | Driver choice / consent | KDE | Video / games | Suspend / resume | HDR / VRR |
| --- | --- | --- | --- | --- | --- |
| NVIDIA | Untested | Untested | Untested | Untested | Untested |
| AMD Radeon | Untested | Untested | Untested | Untested | Untested |
| Intel GPU | Untested | Untested | Untested | Untested | Untested |
| Hybrid GPU | Untested | Untested | Untested | Untested | Untested |

Confirm that no driver is installed or replaced without explicit consent.
Record installed GPU driver, fullscreen/game behavior, monitor resolution,
refresh rate, acceleration and color output.

## Performance, memory and recovery

Read-only diagnostic commands, compatible with fish and ordinary POSIX shells:

```sh
skaldr-version --json
skaldr-doctor --json
uname -r
free -h
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS,MODEL
systemctl status scx_loader.service --no-pager
systemctl status snapper-timeline.timer --no-pager
systemctl status snapper-cleanup.timer --no-pager
```

- [ ] Verify `scx_lavd` actually runs when supported, and that the built-in
      kernel scheduler remains available without `sched_ext`.
- [ ] Verify sustained CPU/GPU thermals, power profiles and suspend/resume.
- [ ] Check the swappiness policy and *actual* ZRAM presence/size for available
      8/16/32/64 GB RAM systems. Mark unavailable scenarios **untested**.
- [ ] Verify Snapper's root configuration, real snapshots, cleanup and timers.
- [ ] Test snapshot rollback **only** on disposable data with known-good backup.
- [ ] Test kernel LTS and bootloader recovery entries after a cold boot.

## Known limitations and reporting

The successful CI installer logs contain non-blocking warnings about optional
systemd units (CUPS, virtualization guests, firewall and ZFS services) and the
missing `chcon` utility. These have **not** been independently audited on
physical hardware. An installed system can pass automated login while still
having hardware-specific issues.

| Report field | Tester result |
| --- | --- |
| Test date and exact preview version | |
| Hardware, firmware, GPU and RAM | |
| Filesystem and bootloader | |
| Tested procedure | |
| Pass / fail / untested | |
| Expected and actual behavior | |
| Relevant sanitized logs | |

When collecting logs use `journalctl -b -p warning --no-pager`,
`systemctl --failed`, and `skaldr-doctor --json` as starting points.
Redact personal data, serial numbers, user paths and credentials before
sharing. Never submit the whole Calamares log without reviewing it.

**Do not promote this preview to stable** until real hardware compatibility,
recovery and release-mode ISO verification are documented.
