# Skaldr OS v0.1.0-preview.2 — release candidate

**Status:** technically validated; **NOT PUBLISHED**. This document prepares a
manual development-preview release. It does not grant permission to publish a
stable release or silently replace v0.1.0-preview.1.

## Exact release identity

| Field | Value |
| --- | --- |
| Proposed tag | `v0.1.0-preview.2` |
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

## Required manual publication gate

Before publishing, recheck that the source checks and all five ISO jobs for
the exact source SHA above are successful, that the artifact is still
available, and that no tag `v0.1.0-preview.2` already exists. Review the
release notes and the unsupported scenarios below.

To publish this validated development candidate, open the
[manual release workflow](https://github.com/pomercier/Skaldr-OS/actions/workflows/skaldr-release.yml),
select **Run workflow**, keep `master`, and use the prefilled
`v0.1.0-preview.2` version with `stable=false`. Leave the
optional `source_sha` **empty**: the workflow now derives it automatically
from this candidate's trusted `docs/PUBLIC-PREVIEW-2-LOCK.json` instead
of from newer documentation-only master commits. A mismatched explicit SHA
is still rejected. This action publishes seven files and is not performed
automatically by a source push.

Alternatively, use the same workflow explicitly from the terminal:

```sh
gh workflow run skaldr-release.yml --ref master \
  -f version=v0.1.0-preview.2 \
  -f stable=false \
  -f source_sha=e37fdd25e01e9564223f426c3ff4000dbdd5ef5b
```

The release workflow itself must reject non-validated commits or stable
releases. A later documentation-only commit on master must **not** replace
`source_sha`: artifacts correspond to the exact tested revision.

### Independent verification immediately after publication

The release workflow now pins `v0.1.0-preview.2` to
`docs/PUBLIC-PREVIEW-2-LOCK.json` **before** publishing. A **separate runner
job**, gated on successful release publication, downloads all seven GitHub
Release assets, validates their exact source commit and checksums against the
original five-job ISO CI, then reconstructs the complete ISO.

This post-publication job belongs to the **same release workflow**. GitHub
normally suppresses follow-on workflow triggers from an event created by
`GITHUB_TOKEN`, so relying only on `release: published` would not reliably
start the verifier. The optional
[`preview.2 standalone checker`](../.github/workflows/skaldr-preview2-public-verification.yml)
also supports manual dispatch and releases published with non-workflow
credentials. Neither checker edits repository branches, tags, or releases.

The original CI manifest pinned all three part SHA-256 values and the four
helper-file SHA-256 values. It did not record the exact byte length of the
last ISO part in the small verification ZIP; the checker therefore requires
its SHA-256, expected filename, and a size strictly below 2 GiB, rather
than inventing a byte length. The reconstructed full ISO SHA-256 is always
required.

**Status: newest source and ISO checks passed; publication is still pending, so
independent checks of public preview.2 assets cannot yet run.** Do not
mark the public download test complete until the new job reports success.

## Known limits

Physical NVIDIA/AMD/Intel GPU coverage, HDR/VRR/audio/suspend on specific
computers, legacy BIOS installation (only BIOS *live* boot is validated),
Secure Boot, LUKS-encrypted installations, unexpected partition layouts,
automated end-user bootloader rollback, sudden power-loss recovery and
physical-system restoration are **not certified**.

The rollback tested here is a manual CI-only procedure on a disposable VM,
not an automatically deployed user rollback button. Continue to keep the
prior public preview available and label this as a development preview.
