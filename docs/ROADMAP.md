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
- [x] Fail-closed Calamares configuration preflight with isolated YAML integration regression tests (2026-11-13)
- [ ] Validate KDE-only Calamares, custom branding and local diagnostic export with the real packaged installer in the next full ISO CI
- [x] Add isolated KDE-only/branding regression tests; keep stock internal package identifiers for upstream compatibility

## Phase B — hardware and performance
- [x] Vendor-neutral `chwd` driver selection, requiring consent
- [x] Configure preferred `scx_lavd`, Gaming and power Performance policies
- [x] Guard scx_loader boot service when the running kernel lacks sched_ext; verify the diagnostic report in isolated tests (2026-11-13)
- [ ] Verify scheduler failures and built-in kernel fallback on real Intel/AMD hardware
- [x] Conditional Snapper root configuration and cleanup/timeline timers
- [ ] Verify bootloader snapshot restore with supported loaders
- [ ] LTS kernel recovery entry and bootloader verification
- [ ] LACT validation and thermal diagnostics
- [ ] Complete the [physical hardware test matrix](HARDWARE-TESTING.md), including NVIDIA/AMD/Intel coverage
- [ ] Test memory policy and ZRAM on multiple RAM capacities

## Phase C — installed user experience
- [x] KDE default and initial NumLock settings
- [x] Initial system health inspector and KDE control center
- [x] Games, creative tools, office, multimedia and development package manifest
- [ ] Setup wizard, Btrfs snapshots UI and sustained performance monitoring
- [ ] HDR/VRR, suspend, codec hardware acceleration test matrix
- [ ] Validate bundled checksum-verified official ArtCraft Launcher AppImage on the live and installed KDE desktop
- [ ] Distribution-first update frontend

## Phase D — brand, updates and quality
- [x] Rename ISO profile and boot labels without renaming official kernel binaries
- [x] Define installed/live Skaldr OS identity metadata
- [ ] Add approved logo and wallpaper assets as real repository files
- [ ] Verify vector KDE wallpaper, Calamares and BIOS/GRUB splash branding in live VM screenshots after new ISO build
- [ ] Secure and test upstream synchronization before it pushes
- [x] Generate ISO SHA256SUMS and source provenance (run 43367190468)
- [x] Verify full-size ISO split and reconstruction against the original SHA256SUMS (2026-11-13, run 43507233020)
- [x] Publish v0.1.0-preview.1 with seven complete assets and hashes matching the original CI manifests (2026-11-13, release run 43518541485)
- [ ] Independently download and reassemble all public release assets on a second machine
- [x] Authorize development preview only after source checks and all five ISO tests passed for commit b391fc35
- [ ] Publish a stable release only after physical hardware tests and a release-mode ISO build

The user-selected `mitigations=off` default reduces CPU security mitigations.
Maintain a recoverable boot path without this flag.
