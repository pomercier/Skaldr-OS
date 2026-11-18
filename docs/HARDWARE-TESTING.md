# Skaldr OS — physical hardware validation

**Newest publicly released and VM-validated ISO:**
[Skaldr OS v0.1.0-preview.3](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3),
published November 18, 2026. It contains the exact dev.149 image described below
and is available as seven permanent GitHub Release assets. All seven were
independently downloaded, checked and reconstructed with matching SHA-256
([verification run 44389469997](https://github.com/pomercier/Skaldr-OS/actions/runs/44389469997)).
Independently verify
all three parts and the complete ISO SHA-256 with the bundled
`reassemble-skaldr-iso.py` before writing any USB drive.

**Exact development image (November 17, 2026):**
[`skaldr-0.1.0-dev.149-x86_64.iso`](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698/artifacts/14364619884)
from exact Skaldr commit `1b4c3d0c4be1b828edbfd3e202e97a13f0ddb89f`.
This CI artifact passed [154/154 source checks](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284682)
and [5/5 ISO validation jobs](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698),
including real ArtCraft graphical launch on installed KDE. Its SHA-256 is
`e29503551ba643d93e5d0137c06ba0ea22dbeb55c6fde335537bebc7f92cd4f9`.
The CI artifact itself is temporary; download the permanent [preview.3 release](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3) or verify via
[the dev.149 instructions](../README.md#latest-vm-validated-development-iso--dev149)
and keep the ISO + `SHA256SUMS` together. **Do not mix dev.149 files with
preview.2.**

The previous publicly released, VM-validated image is
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
- [ ] Download the permanent [v0.1.0-preview.3 release](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3), **all seven files**: the three `dev.149` ISO parts, `SHA256SUMS`, `SHA256SUMS.parts`, `ASSEMBLE.txt` and `reassemble-skaldr-iso.py`.
- [ ] Keep the seven files together, reconstruct and verify:
  
```sh
python3 reassemble-skaldr-iso.py reassemble --directory .
sha256sum -c SHA256SUMS
```

- [ ] Confirm exact full ISO SHA-256:
  `e29503551ba643d93e5d0137c06ba0ea22dbeb55c6fde335537bebc7f92cd4f9`
  (4,194,566,144 bytes). **Never flash a split `.partNNN` file.**
- [ ] Consult the [machine-readable release evidence and stable blockers](RELEASE-READINESS.md). A passing VM job is not proof of physical compatibility.
- [ ] Never mix assets from preview.1, preview.2 and preview.3.

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

## Privacy-limited hardware observations

**For upcoming development builds** containing the tool, use `skaldr-hardware-probe`
or `skaldr-hardware-probe --write ~/skaldr-hardware.json` on the actual system.
The existing **preview.3 does not contain this new tool**; the first later
fully validated ISO that includes the commit may be used instead. The probe is
read-only, does not need root privileges, uploads nothing and writes new reports
with private file permissions. It records broad GPU vendor families, boot mode,
RAM, session and exact Skaldr revision while deliberately omitting identifying
device addresses, hostnames, usernames, serials, networks and logs.

A probe report is **not a physical installation test, GPU certification or
verification of HDR/VRR**, and should never mark a stable-release evidence
checkbox as passed automatically. Confirm actual tests manually, then review
the report for privacy before sharing it.

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
