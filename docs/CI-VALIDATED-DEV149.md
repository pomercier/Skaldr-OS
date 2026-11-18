# Skaldr OS dev.149 — fully tested development ISO (November 17, 2026)

**Validation: PASS**. **This exact `dev.149` ISO is now permanently published**
as [`v0.1.0-preview.3`](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3)
(seven public assets, 2026-11-18). It was not rebuilt for publication.
The **independent public-download SHA-256 check PASSED**: a separate
Ubuntu runner fetched all seven public assets, validated public tag metadata,
checked all ISO parts, and rebuilt the original ISO with the exact
`e2950355...` hash ([run 44389469997](https://github.com/pomercier/Skaldr-OS/actions/runs/44389469997);
[proof artifact 14467203750](https://github.com/pomercier/Skaldr-OS/actions/runs/44389469997/artifacts/14467203750)).

This is the newest fully VM-tested development ISO in
[GitHub Actions run 44164284698](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698),
also a permanent public GitHub Release; GitHub Actions artifacts themselves
still expire and may require authentication.

- ISO: `skaldr-0.1.0-dev.149-x86_64.iso`
- Exact Skaldr source: `1b4c3d0c4be1b828edbfd3e202e97a13f0ddb89f`
- Verified upstream Calamares source: `255a96ed16dbb73ceb535ddf2e18b5f07f0b2cc7`
- Full ISO SHA-256: `e29503551ba643d93e5d0137c06ba0ea22dbeb55c6fde335537bebc7f92cd4f9`
- [Complete ISO artifact](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698/artifacts/14364619884)
- [Independent ISO reassembly/checksum report](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698/artifacts/14368286299)
- [Source checks: 154/154](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284682)
- [Independent installed ArtCraft recheck on prior ISO: PASS](https://github.com/pomercier/Skaldr-OS/actions/runs/44163757616)

## Exact verified functional coverage

All **five** steps of the ISO build/test/reassembly workflow passed.

| Test job | Evidence | Result |
| --- | --- | --- |
| Build | Rebuilt Calamares; recorded actual upstream source SHA; produced `dev.149` | PASS |
| UEFI GRUB/ext4 | Installed with Calamares, booted KDE, checked native Control Center and ArtCraft AppImage checksum; found title `ARTCRAFT`, `AniCraft`, `AVAILABLE TO INSTALL` in real graphical app | PASS |
| UEFI Limine/Btrfs | Installed, powered off, independently restored an offline Btrfs snapshot, cold-booted guest and verified original state from KDE | PASS |
| BIOS/live | Reached live KDE installer desktop with legacy BIOS firmware | PASS |
| ISO integrity | Downloaded complete 4+ GB ISO, checked SHA-256, split and reassembled; verified original checksum again | PASS |

An additional ArtCraft-only GitHub Actions workflow re-ran installation and
the real native GUI on the previous exact ISO artifact **without rebuilding
Calamares**, also PASS. This removes the old false-negative OCR test and
allows UI assertions to be independently validated.

## Download and verify on CachyOS (fish-compatible)

```sh
sudo pacman -S --needed github-cli
gh auth login
mkdir -p "$HOME/Downloads/Skaldr-OS"
gh run download 44164284698 --repo pomercier/Skaldr-OS --name skaldr-os-x86_64-261117 --dir "$HOME/Downloads/Skaldr-OS"
cd "$HOME/Downloads/Skaldr-OS"
sha256sum -c SHA256SUMS
```

Only the complete `.iso` is bootable. Read [hardware testing guidance](HARDWARE-TESTING.md)
before writing any removable media. Do not use this development ISO to
overwrite a production system.

## Not yet proved

- Real NVIDIA RTX 3080, AMD or Intel graphics, GPU driver switching, HDR/VRR, suspend/resume.
- Physical UEFI installation, storage layouts beyond the CI cases, secure boot
  and encrypted installation.
- ArtCraft *live-session* launch; installed KDE launch alone passed.
- Long-term reliability on actual user hardware.

The latest **public GitHub Release** is
[`v0.1.0-preview.3`](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3)
containing this same validated `dev.149` image. The older
[`v0.1.0-preview.2`](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2)
remains archived with its independently verified `dev.129` ISO.
