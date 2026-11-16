# Skaldr OS v0.1.0-preview.2 — release candidate

**Status:** technically validated; **NOT PUBLISHED**. This document prepares a
manual development-preview release. It does not grant permission to publish a
stable release or silently replace v0.1.0-preview.1.

## Exact release identity

| Field | Value |
| --- | --- |
| Proposed tag | `v0.1.0-preview.2` |
| Git source SHA | `a0198f8bb864d9774d6118e7fc42ccc58b610a5a` |
| Embedded ISO version | `0.1.0-dev.114` |
| ISO filename | `skaldr-0.1.0-dev.114-x86_64.iso` |
| ISO original SHA-256 | `b31d0a3ce45f6d75e5dbe790218a044523b92a82cc56e4a211be881976b53610` |
| Source tests | [43768508332](https://github.com/pomercier/Skaldr-OS/actions/runs/43768508332) — 134/134 PASS |
| Full ISO validation | [43768508315](https://github.com/pomercier/Skaldr-OS/actions/runs/43768508315) — 5/5 jobs PASS |
| Isolated installed rollback | [43768508288](https://github.com/pomercier/Skaldr-OS/actions/runs/43768508288) — PASS |
| Previous public preview | [v0.1.0-preview.1](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1) — all seven public assets independently downloaded and SHA-256-reassembled ([run 43780766882](https://github.com/pomercier/Skaldr-OS/actions/runs/43780766882)) |

The source is 52 commits ahead of preview.1 (84 changed files in the GitHub
comparison as reviewed on November 15, 2026). This is a development preview,
**not a hardware-certified release**.

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
- Fixed CachyOS upstream sync discovery without unauthenticated GitHub API
  rate limits; preserved the single `master` branch.
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
1c9e94104fa7b580b548eff6ee89d00c54d7a964c4a24a3007950470538876c1  skaldr-0.1.0-dev.114-x86_64.iso.part001
2d777245c9f70068e7755b2790d98919afdeab59bb69486c23c493ce6d6593b3  skaldr-0.1.0-dev.114-x86_64.iso.part002
1b9e7e85bb4d8a13d70414a82a235a3c73e6b05bb5bba79f44d913df66fa4aa3  skaldr-0.1.0-dev.114-x86_64.iso.part003
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

If explicitly authorized to publish, use the existing
[manual release workflow](../.github/workflows/skaldr-release.yml):

```sh
gh workflow run skaldr-release.yml --ref master \
  -f version=v0.1.0-preview.2 \
  -f stable=false \
  -f source_sha=a0198f8bb864d9774d6118e7fc42ccc58b610a5a
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

**Status: prepared, not yet executed against a public preview.2.** Do not
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
