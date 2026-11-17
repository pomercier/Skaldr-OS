# Skaldr OS — physical hardware validation

The newest publicly released, VM-validated image is
[`Skaldr OS v0.1.0-preview.2`](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2),
embedding `skaldr-0.1.0-dev.129-x86_64.iso` from source commit
`e37fdd25e01e9564223f426c3ff4000dbdd5ef5b`.
It passed [148 source tests](https://github.com/pomercier/Skaldr-OS/actions/runs/43924758916)
and [five ISO validation jobs](https://github.com/pomercier/Skaldr-OS/actions/runs/43924758899)
on November 16, 2026, including installed KDE login, Calamares installation
with GRUB/ext4 and Limine/Btrfs, offline rollback and ISO reassembly.

**This is a public development preview, not a certified production system.**
All seven published assets were independently downloaded and reassembled with
matching SHA-256 on [GitHub Actions run 43996058008](https://github.com/pomercier/Skaldr-OS/actions/runs/43996058008).

## Before installing

- [ ] Use a spare computer or disposable test SSD, **not the only system drive**.
- [ ] Verify independent data backups and keep a bootable rescue medium.
- [ ] Download **all seven files** from
      [the public preview.2 release](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2).
      Keep `.iso.part001`, `.part002`, `.part003`, `SHA256SUMS`,
      `SHA256SUMS.parts`, `ASSEMBLE.txt`, and
      `reassemble-skaldr-iso.py` together.
- [ ] Run `python3 reassemble-skaldr-iso.py reassemble --directory .`
      and then `sha256sum -c SHA256SUMS`. Confirm the complete ISO matches
      exactly:

```text
177b5667b29338db66473ebefb739551ee35edb116cd6b650e2ec6d9f4517b2e
```

- [ ] If testing the older public `preview.1` instead, download all seven
      public Release files and reconstruct its ISO using the matching
      `reassemble-skaldr-iso.py` and checksums. **Never mix preview versions.**

- [ ] Record CPU, RAM, GPU model/vendor, storage, firmware UEFI/BIOS mode and
      Secure Boot state before testing.

## Installation and boot

- [ ] Write **only the fully verified .iso** to a spare USB device with a
      trusted image writer. The destination device will be overwritten;
      confirm it is not a system drive before writing.
- [ ] Boot the live ISO, open the installer and explicitly verify the target drive.
- [ ] Install **GRUB/ext4** onto a disposable drive; cold boot without the ISO.
- [ ] Separately install **Limine/Btrfs**; cold boot without the ISO.
- [ ] Confirm account password is required and KDE Plasma launches.
- [ ] Confirm Skaldr branding on the installed Plasma Login screen and
      confirm `skaldr-control-center` opens with Overview and system details.
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
