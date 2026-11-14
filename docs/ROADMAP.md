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
- [x] Implement opt-in snapshot-before-pacman updater, fail-closed on Btrfs (source-level tests)
- [x] Implement persistent Balanced/Gaming/Creator power choices without overclock (source-level tests)
- [x] Add locally generated allowlisted diagnostic report and privacy checks
- [ ] Validate snapshot creation, updates and power modes on real hardware
- [ ] Build a full native Qt6 Control Center and setup wizard, including long-term performance monitoring
- [x] Add read-only GPU/Vulkan/FFmpeg/display inventory with isolated unit tests
- [x] Add read-only recovery readiness report (Snapper, kernel filenames, bootloader presence)
- [x] Create contributor hardware test-report template (no privacy-sensitive identifiers)
- [ ] Validate GPU decoding, HDR/VRR, suspend and recovery on physical machines
- [ ] Validate bundled checksum-verified official ArtCraft Launcher AppImage on the live and installed KDE desktop
- [ ] Expand the safe update workflow into a complete distribution-first update frontend and rollback UX

## Phase D — brand, updates and quality
- [x] Rename ISO profile and boot labels without renaming official kernel binaries
- [x] Define installed/live Skaldr OS identity metadata
- [ ] Add approved logo and wallpaper assets as real repository files
- [x] Add per-ISO measured-size JSON report to every built ISO artifact (implementation and isolated tests)
- [x] Add screenshot hash/OCR cue index to all QEMU test artifacts without disclosing the full OCR text (isolated tests)
- [ ] Approve visual appearance using fresh VM screenshots and a known-good baseline
- [ ] Verify vector KDE wallpaper, Calamares and BIOS/GRUB splash branding in live VM screenshots after new ISO build
- [x] Replace rate-limited unauthenticated REST default-branch discovery with official Git symbolic HEAD and fail-closed regression tests
- [ ] Verify the repaired upstream synchronization in a live GitHub Actions run before claiming automatic merging is restored
- [x] Generate ISO SHA256SUMS and source provenance (run 43367190468)
- [x] Verify full-size ISO split and reconstruction against the original SHA256SUMS (2026-11-13, run 43507233020)
- [x] Publish v0.1.0-preview.1 with seven complete assets and hashes matching the original CI manifests (2026-11-13, release run 43518541485)
- [ ] Independently download and reassemble all public release assets on a second machine
- [x] Authorize development preview only after source checks and all five ISO tests passed for commit b391fc35
- [ ] Publish a stable release only after physical hardware tests and a release-mode ISO build

The user-selected `mitigations=off` default reduces CPU security mitigations.
Maintain a recoverable boot path without this flag.
