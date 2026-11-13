# Skaldr OS implementation plan

The phases below are ordered to minimize regression risk. An item is complete
only when tested; the existence of code is not evidence of successful boot.

## Phase A — boot and installation reliability
- [x] Correct NumLock and the collision with `cachyos-kde-settings`
- [x] Replace cascade-removal of dependencies with guarded cleanup
- [x] Successful ISO build, generated checksum and UEFI installation smoke tests (2026-11-13; run 43367190468)
- [x] Legacy BIOS live-ISO boot smoke test (SeaBIOS, no OVMF, desktop and installer detected; 2026-11-13, run 43465976353)
- [x] Complete Calamares install and cold reboot in a UEFI VM (GRUB/ext4 and Limine/Btrfs; 2026-11-13, run 43367190468)
- [x] Log in to installed KDE Plasma and verify the first-run Skaldr welcome (both scenarios; run 43367190468)
- [ ] Automated integration tests against actual Calamares module configuration

## Phase B — hardware and performance
- [x] Vendor-neutral `chwd` driver selection, requiring consent
- [x] Configure preferred `scx_lavd`, Gaming and power Performance policies
- [ ] Test scheduler compatibility and automatic safe fallback on non-supporting CPUs
- [x] Conditional Snapper root configuration and cleanup/timeline timers
- [ ] Verify bootloader snapshot restore with supported loaders
- [ ] LTS kernel recovery entry and bootloader verification
- [ ] LACT validation and thermal diagnostics
- [ ] Test memory policy and ZRAM on multiple RAM capacities

## Phase C — installed user experience
- [x] KDE default and initial NumLock settings
- [x] Initial system health inspector and KDE control center
- [x] Games, creative tools, office, multimedia and development package manifest
- [ ] Setup wizard, Btrfs snapshots UI and sustained performance monitoring
- [ ] HDR/VRR, suspend, codec hardware acceleration test matrix
- [ ] Native ArtCraft package and distribution-first update frontend

## Phase D — brand, updates and quality
- [x] Rename ISO profile and boot labels without renaming official kernel binaries
- [x] Define installed/live Skaldr OS identity metadata
- [ ] Add approved logo and wallpaper assets as real repository files
- [ ] Apply logo to desktop, Calamares, splash, boot and social preview
- [ ] Secure and test upstream synchronization before it pushes
- [x] Generate ISO SHA256SUMS and source provenance (run 43367190468)
- [ ] Verify a full-size ISO split and reconstructed with its original SHA256SUMS (automated CI gate implemented; awaiting run)
- [ ] Validate a split preview-release upload and reassembly on GitHub Releases
- [ ] Authorize a development preview only after passing the latest full ISO CI
- [ ] Publish a stable release only after physical hardware tests and a release-mode ISO build

The user-selected `mitigations=off` default reduces CPU security mitigations.
Maintain a recoverable boot path without this flag.
