# Skaldr OS implementation plan

The phases below are ordered to minimize regression risk. An item is complete
only when tested; the existence of code is not evidence of successful boot.

## Phase A — boot and installation reliability
- [x] Correct NumLock and the collision with `cachyos-kde-settings`
- [x] Replace cascade-removal of dependencies with guarded cleanup
- [ ] Successful ISO build, checksum, UEFI and legacy BIOS smoke test
- [x] Complete Calamares install and cold reboot in a UEFI VM (GRUB/ext4 and Limine/Btrfs; 2026-11-13, run 43350558608)
- [ ] Login to the installed KDE Plasma session and verify the first-run Skaldr welcome
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
- [ ] Produce verified ISO hashes, provenance and release candidate builds
- [ ] Publish a release only after clean installation and boot testing

The user-selected `mitigations=off` default reduces CPU security mitigations.
Maintain a recoverable boot path without this flag.
