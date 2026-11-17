# Skaldr OS v0.1.0-preview.2 — published and independently verified

**Status: PUBLISHED DEVELOPMENT PREVIEW**, November 16, 2026 (Quebec time).
[Download the seven public release files](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2).
The exact public files passed an independent full-ISO SHA-256 reconstruction
([run 43996058008](https://github.com/pomercier/Skaldr-OS/actions/runs/43996058008)).
This remains a development preview, not a stable or hardware-certified release.

## Exact release identity

| Field | Value |
| --- | --- |
| Published tag | [`v0.1.0-preview.2`](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2) |
| Git source SHA | `e37fdd25e01e9564223f426c3ff4000dbdd5ef5b` |
| Embedded ISO version | `0.1.0-dev.129` |
| ISO filename | `skaldr-0.1.0-dev.129-x86_64.iso` |
| ISO original SHA-256 | `177b5667b29338db66473ebefb739551ee35edb116cd6b650e2ec6d9f4517b2e` |
| Source tests | [43924758916](https://github.com/pomercier/Skaldr-OS/actions/runs/43924758916) — 148/148 PASS |
| Full ISO validation | [43924758899](https://github.com/pomercier/Skaldr-OS/actions/runs/43924758899) — 5/5 jobs PASS |
| Earlier isolated Btrfs rollback evidence | [43768508288](https://github.com/pomercier/Skaldr-OS/actions/runs/43768508288) — PASS on the preceding source revision; the new ISO also passed its Limine/Btrfs installed-rollback matrix |
| Previous public preview | [v0.1.0-preview.1](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1) — all seven public assets independently downloaded and SHA-256-reassembled ([run 43780766882](https://github.com/pomercier/Skaldr-OS/actions/runs/43780766882)) |

This candidate includes the November 16, 2026 CachyOS upstream merge and the
pinned Calamares staging rebuild. It also includes Skaldr branding at the
installed KDE Plasma login screen, and a targeted exclusion of optional
Haruna to avoid a verified broken KDE dependency chain (`mpvqt` / `mpv` /
`libplacebo`). VLC remains included. Its five-job ISO matrix passed for the exact
source commit above. This remains a development preview, **not a
hardware-certified release**.

## Changes since preview.1

- KDE Plasma-only Calamares choices and consistent Skaldr OS visual identity,
  including a scalable GitHub emblem, high-resolution wallpaper and dedicated
  SVG artwork in Calamares.
- Native PySide6/Qt6 Skaldr Control Center with Overview, Performance,
  Graphics, Recovery, Applications and About pages; the existing KDE
  `kdialog` menu remains a fallback.
- Explicitly authorized Balanced/Gaming/Creator profiles and
  snapshot-guarded Btrfs system updates. No automatic GPU overclock and no
  privileged change without user confirmation.
- Privacy-limited local diagnostics, vendor-neutral GPU/Vulkan information
  and recovery-readiness reporting.
- Updated local ArtCraft Launcher integration with checksum checks.
- Fixed actual Calamares installation failures in both GRUB/ext4 and
  Limine/Btrfs caused by upstream Haruna's `libplacebo.so=387-64`
  dependency; VLC is retained.
- Applied the Skaldr OS wallpaper to installed KDE Plasma Login without
  changing passwords or autologin settings.
- Resolved the CachyOS 26.11 merge conflicts, preserved the single `master`
  branch, migrated to the pinned `cachyos-calamares-staging` package and
  retained Skaldr's fail-closed installer without destructive keyring resets.
- Incorporated upstream UEFI shell, Memtest86+ and GRUB live-boot fixes.
- Expanded QEMU testing: actual Calamares installations, cold boots, installed
  KDE logins and native Control Center display for GRUB/ext4 and Limine/Btrfs.
- **New recovery evidence:** the disposable Calamares-installed Limine/Btrfs
  VM is backed up and restored from a read-only root snapshot, then boots
  again without the installer ISO; KDE authenticates and the guest confirms
  the original pre-rollback state. Its original disposable QCOW2 remains
  separate until verification.
- Real SHA-256 verification of the multi-gigabyte ISO, its three split
  release parts, and reassembly of an identical ISO.

## ISO assembly files and integrity

The successful validation produced a ZIP containing `SHA256SUMS`,
`SHA256SUMS.parts`, `ASSEMBLE.txt`, and `reassemble-skaldr-iso.py`.
The three ISO part hashes in the verified manifest are:

```text
b781b2dcdc94374a865b17a7614c2d7f2f50d7195c46625629b4634a62809e52  skaldr-0.1.0-dev.129-x86_64.iso.part001
8fe7cfea0e1fd8815c948140295c0d324c3ce7f3df650ba9243742880f64dfe4  skaldr-0.1.0-dev.129-x86_64.iso.part002
ab2855a15b516331442d5fbd8f92943c835d1b14ecc3462659e67bd584463fc9  skaldr-0.1.0-dev.129-x86_64.iso.part003
```

After downloading **all** assets into one directory:

```sh
python3 reassemble-skaldr-iso.py reassemble --directory .
sha256sum -c SHA256SUMS
```

**Do not flash .part001, .part002 or .part003 directly.** Only use the
reassembled and verified `.iso`.

## Completed publication and independent verification

The existing fail-closed [release workflow](../.github/workflows/skaldr-release.yml)
published this exact ISO in the second attempt of
[run 43996058008](https://github.com/pomercier/Skaldr-OS/actions/runs/43996058008).
An initial GitHub `GITHUB_TOKEN` release attempt was denied by HTTP 403
while the default branch's workflow files differed from those in the tested
source. After aligning the workflow files to the validated `e37fdd25`
revision, the next attempt passed all checks and published the release
without changing or rebuilding the ISO.

The public tag points to the exact tested source SHA, rather than a later
documentation commit. All seven public asset SHA-256 digests and sizes match
[the immutable release lock](PUBLIC-PREVIEW-2-LOCK.json).

The separate Ubuntu runner job in the same successful release workflow
downloaded **all seven actual public release files**, validated the tag,
part digests and helper files, reconstructed the 4 GiB ISO, and verified its
SHA-256 as:

```text
177b5667b29338db66473ebefb739551ee35edb116cd6b650e2ec6d9f4517b2e
```

**Publication: PASS. Independent public-download and reassembly: PASS.**
Both jobs in run 43996058008 completed successfully. The independent
verification report is archived as
`skaldr-published-preview2-integrity` in that workflow's artifacts.

For testing, download all three `.iso.part*` files and the four helpers
from the [public preview.2 release](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2),
then run `python3 reassemble-skaldr-iso.py reassemble --directory .`.
Only flash the resulting verified `.iso`; never flash an individual part.

## Known limits

Physical NVIDIA/AMD/Intel GPU coverage, HDR/VRR/audio/suspend on specific
computers, legacy BIOS installation (only BIOS *live* boot is validated),
Secure Boot, LUKS-encrypted installations, unexpected partition layouts,
automated end-user bootloader rollback, sudden power-loss recovery and
physical-system restoration are **not certified**.

The rollback tested here is a manual CI-only procedure on a disposable VM,
not an automatically deployed user rollback button. Continue to keep the
prior public preview available and label this as a development preview.
