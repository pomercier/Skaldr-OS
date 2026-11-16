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
- [x] Validate KDE-only Calamares, custom branding and installed KDE welcome with GRUB/ext4 and Limine/Btrfs in the full ISO (2026-11-14, run 43556906661); local log export still requires a focused privacy audit
- [x] Add isolated KDE-only/branding regression tests; keep stock internal package identifiers for upstream compatibility

## Phase B — hardware and performance
- [x] Vendor-neutral `chwd` driver selection, requiring consent
- [x] Configure preferred `scx_lavd`, Gaming and power Performance policies
- [x] Guard scx_loader boot service when the running kernel lacks sched_ext; verify the diagnostic report in isolated tests (2026-11-13)
- [ ] Verify scheduler failures and built-in kernel fallback on real Intel/AMD hardware
- [x] Conditional Snapper root configuration and cleanup/timeline timers
- [x] Validate real Snapper snapshot creation and independent Btrfs data restoration in a disposable 512 MiB image (2026-11-15, run 43683236789)
- [x] Validate restored default-subvolume root selection after remount of the disposable Btrfs image (2026-11-15, run 43736814304)
- [x] Verify explicit `subvol=` mount precedence in disposable CI and add read-only installed rootflags diagnostics (2026-11-15, recovery run 43738627267; source run 43738627201)
- [x] Boot a real Linux kernel with modified and restored Btrfs roots in independent disposable QEMU CI (2026-11-15, run 43740331490, both boots passed)
- [x] Boot real GRUB BIOS rescue media into both modified and restored disposable Btrfs roots (2026-11-15, run 43741230197)
- [x] Boot GRUB rescue ISO through OVMF UEFI into both Btrfs roots (2026-11-15, run 43745598361)
- [x] Boot Limine hybrid BIOS/UEFI rescue media into original and restored Btrfs roots (2026-11-15, run 43746110884)
- [x] Boot Limine from a separate disposable GPT/FAT EFI disk (without ISO) into both Btrfs roots (2026-11-15, run 43747048553)
- [x] Verify guest writes persist separately on original and recovered Btrfs roots, preserving the read-only source snapshot (2026-11-15, QEMU run 43747657935; 12/12 boots passed)
- [x] Audit known GRUB, Limine, systemd-boot and fstab root-subvolume selectors in read-only recovery report (source run 43741230183; not exhaustive)
- [x] Validate offline rollback helper on a standalone synthetic GPT/Btrfs QCOW2 with real qemu-img, loop mounts and source snapshot (2026-11-15, isolated run 43752617397)
- [x] Refuse a hardcoded numeric Btrfs rootflags with unchanged source QCOW2 SHA-256, then validate positive recovery and immutable snapshot (2026-11-15, isolated run 43752897173)
- [x] Recover a real Calamares-installed Limine/Btrfs root on disposable QCOW2, cold reboot without installer ISO, authenticate KDE, verify restored guest marker and reopen Skaldr Control Center (2026-11-15, full independent probe 43753422214 using validated ISO 87)
- [x] Diagnose the 2026-11-15 full-ISO Limine/Btrfs rollback failure: Calamares installation and KDE Control Center passed, but offline loop-backed `blkid` partition discovery found no Btrfs partition (run 43758327044)
- [x] Confirm deterministic GPT/Btrfs magic detection in isolated QCOW2 smoke (run 43768508288) and in the exact-source Limine/Btrfs full ISO matrix (run 43768508315; November 15, 2026)
- [x] Complete Calamares-installed Limine/Btrfs rollback from the exact source revision `a0198f8`, cold-boot the restored guest into KDE and pass all five ISO jobs (run 43768508315)
- [ ] Verify recovery with other supported bootloaders, rootflags configurations, encrypted layouts and adverse reboot scenarios
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
- [x] Implement native PySide6/Qt6 Control Center with six pages, polkit-gated actions, explicit confirmations and kdialog fallback (initial source/CI validation)
- [x] Add installed-KDE GUI launch with KRunner and screenshot/OCR assertion to both UEFI Quicktest installation paths (real ISO execution pending)
- [x] Confirm installed Qt6 Control Center opens and shows live system/kernel diagnostics on both UEFI VMs (run 43648608032; visual evidence verified; exact OCR check pending revalidation)
- [x] Pass full 5/5 ISO CI including native Qt6 dashboard verification (2026-11-15, run 43683236835)
- [ ] Audit Qt6 accessibility and build a guided setup wizard
- [x] Add read-only GPU/Vulkan/FFmpeg/display inventory with isolated unit tests
- [x] Add read-only recovery readiness report (Snapper, kernel filenames, bootloader presence)
- [x] Create contributor hardware test-report template (no privacy-sensitive identifiers)
- [ ] Validate GPU decoding, HDR/VRR, suspend and recovery on physical machines
- [x] Update the locally bundled ArtCraft Launcher to upstream v0.19.2 with published SHA-256, local diagnostics and no web redirect in the wrapper (2026-11-15, source checks run 43758327030)
- [ ] Validate bundled checksum-verified official ArtCraft Launcher AppImage on the live and installed KDE desktop
- [ ] Expand the safe update workflow into a complete distribution-first update frontend and rollback UX

## Phase D — brand, updates and quality
- [x] Rename ISO profile and boot labels without renaming official kernel binaries
- [x] Define installed/live Skaldr OS identity metadata
- [ ] Add approved logo and wallpaper assets as real repository files
- [x] Add per-ISO measured-size JSON report to every built ISO artifact (implementation and isolated tests)
- [x] Add a Quicktest video SHA-256 index and bounded screenshot extraction, since archived recordings replace temporary PPM screenshots; source-level regression tests added
- [ ] Approve visual appearance using new CI frame samples and a documented known-good baseline (manual review still required)
- [x] Replace cropped Calamares productWelcome 4K wallpaper with a dedicated 880x340 SVG and QML fallback (source tests; full ISO validation pending)
- [ ] Verify vector KDE wallpaper, Calamares, BIOS/GRUB splash and installed Plasma Login branding in a NEW full ISO (greeter test and wallpaper policy implemented; CI pending)
- [x] Replace rate-limited unauthenticated REST default-branch discovery with official Git symbolic HEAD and fail-closed regression tests
- [x] Verify repaired upstream synchronization in GitHub Actions (2026-11-15, run 43669141527)
- [x] Generate ISO SHA256SUMS and source provenance (run 43367190468)
- [x] Verify full-size ISO split and reconstruction against the original SHA256SUMS (2026-11-13, run 43507233020)
- [x] Publish v0.1.0-preview.1 with seven complete assets and hashes matching the original CI manifests (2026-11-13, release run 43518541485)
- [x] Update [preview.2 candidate release notes](RELEASE-CANDIDATE-PREVIEW-2.md) for validated source `4bf13feb` after the CachyOS 26.11 merge; 147 source tests and 5/5 ISO jobs passed on November 16, 2026; **not published**
- [x] Pin preview.2 release checksums to original 5/5 ISO run, gate publication on matching exact source and CI asset hashes, and configure independent post-publication and optional release-event verification; source regression tests required
- [ ] Publish v0.1.0-preview.2 only via the existing manual release workflow with explicit `source_sha`; require the follow-up public reassembly job to pass
- [x] Independently download all seven public v0.1.0-preview.1 assets on an Ubuntu CI runner, compare to the original five-job ISO manifests, and reassemble the full ISO with SHA-256 verified (2026-11-15, [run 43780766882](https://github.com/pomercier/Skaldr-OS/actions/runs/43780766882))
- [x] Authorize development preview only after source checks and all five ISO tests passed for commit b391fc35
- [ ] Publish a stable release only after physical hardware tests and a release-mode ISO build

The user-selected `mitigations=off` default reduces CPU security mitigations.
Maintain a recoverable boot path without this flag.
