# Skaldr OS implementation plan
- [ ] **P0 / summary OCR and installed-VM qualification:** On the
  2026-11-27 eight-job development and release matrices, the five real
  installer scenarios reached Calamares Summary but failed a brittle OCR
  assertion for "/dev/vda", consistently read as "/devi/vda" in archived
  screenshots. Require the photographed summary explanatory heading and
  the independently visible "Create new" partition action instead.
  Preserve filesystem mount proof, installation, disk-only cold boot,
  authenticated KDE login and eight-job fail-closed gates. No ISO is
  certified until the matrix actually completes successfully.
- [ ] **P0 / real GUI OCR stability in the eight-job matrix:** On
  2026-11-27 both development and release-mode installations failed
  early because the visual OCR read "GMU GRUB" instead of "GNU GRUB",
  and "II IUStratIVE prEVIEW" instead of "Illustrative preview",
  despite genuine photographed menus. Use the separately verified
  "GRUB" menu token and the adjacent "Appearance varies by configuration"
  footer, retaining real partition, install, disk-only boot and KDE
  acceptance. These changes are NOT qualified until all eight CI jobs pass.
- [ ] **P0 / restore proven BIOS model and verify chroot ESP:** The expanded
  eight-job matrix on 2026-11-26 failed BIOS partition navigation with
  "No items in BootLoaderModel". The previous six-job matrix succeeded
  using official unpatched Calamares; quarantine the experimental nested
  Qt reset patch in the production build and restore proven keyboard
  navigation. For rEFInd, confirmed /boot was a separately mounted vfat
  ESP in Calamares serial logs; probe actual FAT with statfs when mountinfo
  in the install chroot cannot resolve findmnt. Both corrections remain
  UNVERIFIED until all eight real VM jobs pass, including disk-only boot.
- [ ] **P0 / rEFInd EFI boot and BIOS partition navigation:** Archived
  VM screenshots confirm successful rEFInd installation followed by an OVMF
  no-bootable-device failure, and an enabled BIOS partition Next control
  that keyboard navigation did not activate. Require a verified UEFI
  fallback on the actual mounted FAT ESP (never overwrite another loader);
  use local QMP to click the real BIOS Next button. Both cases remain
  UNVERIFIED until the complete eight-job VM matrix succeeds.
- [ ] **P0 / Calamares BIOS GUI segfault:** Actual eight-job CI confirmed a
  SIGSEGV after nested and unbalanced Qt BootLoaderModel reset warnings.
  Apply a fail-closed local source patch in the Calamares makepkg prepare()
  hook, preserving the official upstream commit and native GUI tests.
  Correct a separate, proven rEFInd GPT OCR false negative using two actual
  summary-page visual cues. Neither issue is complete until all eight real
  ISO/VM jobs pass successfully.
- [ ] **P0 / additional installed UEFI bootloaders:** Add real VM installation
  and cold boot tests for rEFInd/ext4 and systemd-boot/ext4 in both developer
  and release-mode ISO pipelines. Public release checks now require eight
  successful jobs, including authenticated KDE and installer evidence.
  Treat both as unverified until the new matrix passes. Existing preview.151
  remains the last verified public ISO.
- [x] **P0 / legacy BIOS installed boot:** [development ISO 6/6](https://github.com/pomercier/Skaldr-OS/actions/runs/45263079702) and [release-mode ISO 6/6](https://github.com/pomercier/Skaldr-OS/actions/runs/45263079443) completed on `38c3b8560b43aa2e450d9cb9f16ff1d908a57685`, including SeaBIOS + GRUB/ext4 Calamares installation, installed-disk cold boot, authenticated KDE login and Control Center. Physical BIOS hardware remains untested.
- [x] **P0 / real release-mode VM matrix:** A distinct non-development ISO,
  `skaldr-0.1.0-x86_64.iso`, passed all six tests on `88521c22c9e1d9cf5e4d5c79fb09413eca8f85a7`
  ([run 45462762588](https://github.com/pomercier/Skaldr-OS/actions/runs/45462762588)),
  SHA-256 `da2138bee1693b82e1656c2fffb8eb8811f45ae1498f1d4e05898c830b675d64`.
  This is **not** the stable v1.0.0 artifact; independent physical tests and a
  separately pinned v1 build remain required.
- [x] **P0 / newest public preview:** `v0.1.0-preview.151` passed
  [6/6 real ISO/VM checks](https://github.com/pomercier/Skaldr-OS/actions/runs/45462762559)
  and [independent public asset reconstruction](https://github.com/pomercier/Skaldr-OS/actions/runs/45469323148).
  Its published ISO SHA-256 is
  `c00e1ca5dbccc2137bcfd24bb49d6174394e5919616218b135b475b8d1bd2c5e`.
- [x] **P0 / automated VM installation and boot:** The exact published `v0.1.0-preview.142` ISO passed all five CI jobs on 2026-11-23 ([run 45095760918](https://github.com/pomercier/Skaldr-OS/actions/runs/45095760918)): BIOS live boot, actual Calamares installations with GRUB/ext4 and Limine/Btrfs, cold boots without the live ISO, installed KDE Control Center, Btrfs snapshot rollback, and split ISO reconstruction. This closes the automated VM blocker; **physical installation, recovery and hardware coverage remain unverified**, and the historical manual VM failures are retained as regression context.
- [x] Add an offline, machine-readable stable-release evidence gate and corresponding CI report. Stable publication remains explicitly disabled until physical tests, release-mode build and human review.
- [x] Integrate a read-only, privacy-limited hardware observation command and isolated tests into the next development ISO (source checks passed; full new ISO validation pending).
- [ ] Complete the physical test matrix and attach sanitized proof URLs to [RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json); only then consider a stable tag.
- [x] Publish the exact successful dev.149 ISO from validated source `1b4c3d0` as [public v0.1.0-preview.3](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3) (seven permanent assets; 2026-11-18).
- [x] Independently re-download and verify all seven public preview.3 assets and reassemble exactly 4,194,566,144 bytes with original SHA-256 `e2950355...` on an isolated Ubuntu runner ([run 44389469997](https://github.com/pomercier/Skaldr-OS/actions/runs/44389469997), PASS; [machine-readable report](https://github.com/pomercier/Skaldr-OS/actions/runs/44389469997/artifacts/14467203750)).

The phases below are ordered to minimize regression risk. An item is complete
only when tested; the existence of code is not evidence of successful boot.

## Phase A — boot and installation reliability
- [x] Fix real Calamares package resolution by excluding optional Haruna (mpvqt/mpv/libplacebo ABI incompatibility); VLC retained, GRUB/ext4 and Limine/Btrfs installations both passed in run 43924758899.
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
- [x] Validate **installed-KDE** ArtCraft with exact checksum-pinned official AppImage v0.19.2 and real native catalog GUI (header, AniCraft, installation action) in full source `1b4c3d0` GRUB/ext4 ISO [run 44164284698](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698); isolated reuse of earlier full ISO also [passed](https://github.com/pomercier/Skaldr-OS/actions/runs/44163757616), without recompiling.
- [ ] Validate ArtCraft on a **live** KDE desktop (separately from installed), plus physical NVIDIA/AMD/Intel GPU hardware; these were not covered by QEMU.
- [x] Replace unreliable pins to CachyOS's frequently force-pushed Calamares staging branch with direct official branch selection and a verified **post-build** commit check. Exact Calamares source `255a96ed16dbb73ceb535ddf2e18b5f07f0b2cc7` recorded in `calamares-source.sha` alongside the full `dev.149` ISO; [5/5 ISO jobs passed](https://github.com/pomercier/Skaldr-OS/actions/runs/44164284698).
- [ ] Expand the safe update workflow into a complete distribution-first update frontend and rollback UX

## Phase D — brand, updates and quality
- [x] Rename ISO profile and boot labels without renaming official kernel binaries
- [x] Define installed/live Skaldr OS identity metadata
- [ ] Add approved logo and wallpaper assets as real repository files
- [x] Add per-ISO measured-size JSON report to every built ISO artifact (implementation and isolated tests)
- [x] Add a Quicktest video SHA-256 index and bounded screenshot extraction, since archived recordings replace temporary PPM screenshots; source-level regression tests added
- [ ] Approve visual appearance using new CI frame samples and a documented known-good baseline (manual review still required)
- [x] Confirm post-preview.2 Calamares GRUB and Limine branded previews in real QEMU via `Illustrative preview` OCR assertions; all five ISO jobs and 151 source tests passed ([2026-11-17 run 44013893575](https://github.com/pomercier/Skaldr-OS/actions/runs/44013893575)). Remaining rEFInd/systemd-boot visual checks require focused VM coverage
- [x] Replace cropped Calamares productWelcome 4K wallpaper with a dedicated 880x340 SVG and QML fallback (source tests; full ISO validation pending)
- [x] Validate installed Plasma Login Skaldr wallpaper in real QEMU after Limine/Btrfs rollback (run 43924758899); full five-job ISO suite passed, including KDE, installer, BIOS boot, rollback and identical ISO reassembly. Physical hardware validation is still separate.
- [x] Replace rate-limited unauthenticated REST default-branch discovery with official Git symbolic HEAD and fail-closed regression tests
- [x] Verify repaired upstream synchronization in GitHub Actions (2026-11-15, run 43669141527)
- [x] Generate ISO SHA256SUMS and source provenance (run 43367190468)
- [x] Verify full-size ISO split and reconstruction against the original SHA256SUMS (2026-11-13, run 43507233020)
- [x] Publish v0.1.0-preview.1 with seven complete assets and hashes matching the original CI manifests (2026-11-13, release run 43518541485)
- [x] Document the [published preview.2](RELEASE-CANDIDATE-PREVIEW-2.md) from validated source `e37fdd25` after the CachyOS 26.11 merge; 148 source tests and 5/5 ISO jobs passed on November 16, 2026
- [x] Pin preview.2 release checksums to original 5/5 ISO run, gate publication on matching exact source and CI asset hashes, and configure independent post-publication and optional release-event verification; source regression tests required
- [x] Publish `v0.1.0-preview.2` from exact validated `e37fdd25` using the existing fail-closed release workflow; independently download all seven public files and reconstruct the original image with SHA-256 verified ([run 43996058008](https://github.com/pomercier/Skaldr-OS/actions/runs/43996058008), 2/2 PASS, November 16 Quebec time)
- [x] Independently download all seven public v0.1.0-preview.1 assets on an Ubuntu CI runner, compare to the original five-job ISO manifests, and reassemble the full ISO with SHA-256 verified (2026-11-15, [run 43780766882](https://github.com/pomercier/Skaldr-OS/actions/runs/43780766882))
- [x] Authorize development preview only after source checks and all five ISO tests passed for commit b391fc35
- [ ] Publish a stable release only after physical hardware tests and a release-mode ISO build

The user-selected `mitigations=off` default reduces CPU security mitigations.
Maintain a recoverable boot path without this flag.
