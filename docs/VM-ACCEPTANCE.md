# Skaldr OS — manual virtual-machine acceptance test

This manual checklist supplements GitHub Actions. It separates a **live-ISO
desktop screenshot** from evidence of a complete installation. Record the exact
source version, ISO hash and hypervisor before evaluating the result.

## Preparation

- Use the permanently published [preview.144 release](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.144)
  with its seven matching assets; never mix parts from different releases.
- Preview.144 contains `skaldr-0.1.0-dev.217-x86_64.iso` from exact source
  `bb8939175b24f4ebf30309081603bfa08d650d5d`, SHA-256
  `a4c956b798b0d28e07457563bb41129fc6ad54cf2482ce246f6c28025ecbefcf`.
  Its [five build/installation jobs](https://github.com/pomercier/Skaldr-OS/actions/runs/45245780889)
  and [public ISO reconstruction](https://github.com/pomercier/Skaldr-OS/actions/runs/45252577846)
  passed. Use the bundled reassembly script before the checksum command.
- Verify with `sha256sum -c SHA256SUMS` from the directory containing
  the complete ISO and matching checksum manifest.
- Use a disposable VM disk (at least 40 GiB) and allocate resources adequate
  for the desired desktop experience. Do not attach a physical production disk.
- Record hypervisor/version, firmware UEFI or BIOS, CPU/RAM assigned, virtual
  GPU/controller, and any 3D acceleration or display scaling changes.

## Run and record each gate

| Gate | Required observation | Status |
| --- | --- | --- |
| 1. Boot | ISO boots to an interactive live KDE Plasma desktop | UNTESTED |
| 2. Installer | Calamares launches without fatal error; Skaldr and KDE choice appear | UNTESTED |
| 3. Target disk | Disposable virtual target disk is selected deliberately | UNTESTED |
| 4. Install | Installer completes without package/pacstrap/Calamares failure | UNTESTED |
| 5. Cold boot | Shutdown, detach installation ISO, and cold boot from virtual disk | UNTESTED |
| 6. Login | Installed KDE login is functional and still requires authentication | UNTESTED |
| 7. Identity | `skaldr-version --json` reflects the exact installed build | UNTESTED |
| 8. Diagnostics | `skaldr-doctor --json` returns read-only system information | UNTESTED |
| 9. GUI | Control Center opens; ArtCraft launch is verified independently | UNTESTED |
| 10. Restart | The installed system survives a full reboot | UNTESTED |

Run at least two **separate fresh VM installations** for the combinations
already validated in CI: UEFI + GRUB + ext4, and UEFI + Limine + Btrfs.
The legacy BIOS live boot is a separate proven test. A newly added SeaBIOS +
GRUB + ext4 **installed-disk cold boot** is under CI qualification; keep it
**UNTESTED** for this ISO until the full matrix actually succeeds.
For every test, verify the QEMU firmware and ensure the installation ISO is
detached before restarting from the installed disk. Check recovery
of the Btrfs installation in a disposable clone only; never test rollback
without an independent snapshot/disk backup.

## Evidence and diagnosis

Use `PASS`, `FAIL`, `BLOCKED`, or `UNTESTED` for each gate.
A screenshot shows only its observable state; it does not prove earlier or
later stages unless those stages have independent evidence.

When the live or installed system is available, run these **fish-compatible**
commands individually:

```sh
skaldr-version --json
skaldr-doctor --json
systemctl --failed --no-pager
journalctl -b -p err --no-pager
```

The first two should be recorded with their versions when possible. Review
and redact `journalctl` data before publishing; it may contain machine
identifiers, user paths and networking details. Never copy full Calamares
logs into public issues without privacy review.

For screenshots, record **what stage is visible** (firmware menu, live KDE,
installer, completion, installed greeter, desktop) and whether a fatal error
appears. An unlabeled screenshot must not be treated as a PASS for installation
or physical NVIDIA/AMD/Intel GPU support.

## Verdict

Mark `VM INSTALL VERIFIED` only after gates 1–8 and 10 pass for the selected
bootloader/filesystem. The ArtCraft-specific gate remains separate, to avoid
hiding a functional installation behind an optional application failure.
VM success does not replace real-hardware certification; see
[HARDWARE-TESTING.md](HARDWARE-TESTING.md).

No screenshot or test result in this document is represented as a user-reported
PASS until its observed result has been independently reviewed.
