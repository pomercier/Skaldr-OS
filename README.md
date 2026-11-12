# Skaldr OS

**Skaldr OS** is an evolving, performance-focused Linux distribution project based on the official [CachyOS Live ISO](https://github.com/CachyOS/CachyOS-Live-ISO).

The goal is to keep CachyOS's hardware support, rolling-release foundations, and installation options while developing a consistent, high-performance desktop experience. Skaldr OS is an independent derivative project, not an official CachyOS edition.

> **Project status: early development.** The repository currently contains the upstream CachyOS ISO sources and build tooling. The Skaldr-specific configuration described below is the **target design**, not a set of features already implemented, tested, or released. No finished Skaldr OS ISO has been validated.

## Design principles

- **Upstream first:** retain the official CachyOS source and integrate future upstream changes without discarding local customizations.
- **One permanent branch:** keep the repository focused on its default branch (`master` at present). Any temporary integration or testing branches must be removed after use.
- **KDE by default, choice preserved:** prefer KDE Plasma without removing other desktop environments offered by CachyOS.
- **Live and installed parity:** deliver Skaldr's applications and settings in both the live session and the installed system. Final GPU driver selection is the intentional exception.
- **Hardware-aware configuration:** detect capabilities rather than assuming a particular CPU, GPU, memory size, display, or storage device.
- **Native packages first:** use Arch/CachyOS packages and a suitable AUR helper; do not add Flatpak, Snap, Docker, or similar application/container distribution layers.
- **Keep authentication:** retain passwords and normal account authentication. Do not configure passwordless sudo or automatic login for the installed system.
- **English development history:** write new project comments, documentation, and commit messages in English without rewriting upstream history.

## Current state

| Component | Status |
| --- | --- |
| Official CachyOS Live ISO source | Present; forked from upstream |
| Original ISO build scripts and configurations | Present |
| Original CachyOS installer integration | Present |
| KDE Plasma in the live environment | Inherited from upstream |
| Skaldr OS customizations below | Planned; not yet implemented |
| Automated upstream conflict handling | Planned; not yet installed in this repository |
| Custom ISO builds and hardware validation | Not yet completed |

## Planned Skaldr OS experience

### Desktop and system behavior

| Area | Target behavior |
| --- | --- |
| Desktop environment | KDE Plasma preselected; all other upstream choices remain available |
| Keyboard | Caps Lock enabled by default, including the graphical login experience where supported |
| Authentication | Normal login, lock-screen, sudo, and wallet security retained |
| CPU scheduling | Prefer `scx_lavd` continuously when kernel and scheduler support permit; recover safely when unavailable |
| Performance mode | Prefer Gaming and CPU Performance modes continuously when supported |
| Kernel security mitigations | Apply the explicitly requested `mitigations=off` boot parameter (see security notice) |
| Memory | Set `vm.swappiness=0` when installed physical RAM is at least 32 GiB; use a hardware-appropriate policy below that threshold |
| Compressed swap | Retain ZRAM support; do not assume all systems need the same size |
| Storage and recovery | Preserve CachyOS installation choices and offer Btrfs snapshots where applicable |

The permanent performance preferences are intentional. Hardware detection and safe fallbacks must prevent missing features or unsupported devices from breaking boot or login.

### Applications

The target default installation includes the same software in the live ISO and on the installed system:

| Category | Planned software |
| --- | --- |
| Web browser | Brave instead of Firefox |
| Office | LibreOffice Fresh, updated through the rolling package repositories |
| Gaming | CachyOS-compatible gaming tools and applications |
| Multimedia | Audio, video, codecs, and media tools |
| Development | `cmake`, `make`, `fakeroot`, `git`, Python tools, and other relevant development utilities |
| Package management | `pacman` and `yay` (subject to package availability and build verification) |
| KDE utilities | `kcalc` and standard Plasma applications |
| Creative apps | ArtCraft Launcher, to install and manage compatible ArtCraft applications |
| Virtualization | QEMU/KVM and related management tools |
| GPU tuning | LACT only on hardware and driver combinations it actually supports |

**Not included:** Firefox, `prelink`, `preload`, Flatpak, Snap, Docker, or an automatic GPU overclock. No proprietary application or optional large model should be downloaded without an appropriate installation mechanism and validation.

### GPU driver selection

A **first-boot graphics driver assistant** is planned for the installed system:

1. Detect the installed GPU or GPUs, including NVIDIA, AMD, Intel, virtual GPUs, and mixed-GPU systems.
2. Identify the compatible driver choices using the CachyOS hardware-detection and package-management mechanisms.
3. **Prefer the latest compatible proprietary driver when one is genuinely available**, while presenting an open-source alternative.
4. Fall back to supported open-source drivers when no appropriate proprietary option exists.
5. Confirm the choice before changing drivers and keep a recoverable display configuration.

No universal proprietary driver exists for every GPU. The assistant must never present an unavailable driver as a valid option.

### Security trade-off

Skaldr OS is intended to keep normal authentication enabled. However, the requested `mitigations=off` setting disables multiple CPU vulnerability mitigations and **reduces system security**. This setting is part of the proposed performance-oriented configuration, not a claim of a safe or universally faster default. It must be documented clearly and remain reversible.

## Upstream synchronization policy

The authoritative source is **[CachyOS/CachyOS-Live-ISO](https://github.com/CachyOS/CachyOS-Live-ISO)**, following its actual default branch (`master` at the time of writing).

The intended workflow is to:

1. Detect new commits on upstream's current default branch.
2. Incorporate compatible changes while keeping Skaldr-specific configuration intact.
3. Stop on merge conflicts and request manual arbitration without silently dropping changes.
4. Validate the resulting files, build the ISO, and test boot and installation paths before publishing.
5. Keep only one permanent branch; remove any authorized temporary branches after integration.

**This is a development policy, not an assertion that automatic synchronization or releases are already configured.** Upstream commits and their original authorship will remain unchanged.

## Build from the current source

The commands below use the **existing upstream-derived build system**, not a completed Skaldr OS release. Use a compatible Arch Linux/CachyOS build environment with sufficient free disk space.

```bash
sudo pacman -Syu --needed archiso mkinitcpio-archiso git squashfs-tools grub
git clone https://github.com/pomercier/Skaldr-OS.git
cd Skaldr-OS
./buildiso.sh -h
sudo ./buildiso.sh -p desktop -v -w
```

The build script places generated ISO files under the `out/` directory. Successful compilation, installation, UEFI/BIOS boot, and GPU compatibility are **not yet verified for a Skaldr-branded release**.

## Validation required before the first release

- Verify package availability, legal redistribution, and removal of unwanted packaging systems.
- Verify that the live environment and installed system receive the same applications and configuration.
- Verify that KDE is the default while the upstream desktop choices remain selectable.
- Verify Caps Lock, normal password authentication, performance services, and RAM-dependent swap settings.
- Validate graphics detection and driver choices across NVIDIA, AMD, Intel, virtual machines, and mixed GPU configurations.
- Test UEFI and legacy BIOS boot plus Calamares installation and first boot.
- Verify upstream synchronization, build logs, ISO integrity checksums, and release artifacts.

## Credits and licensing

Skaldr OS builds on the work of the [CachyOS project](https://cachyos.org/) and [Arch Linux](https://archlinux.org/). Original project files retain their respective notices and licenses; see [LICENSE](LICENSE). Acknowledgment of upstream work does not imply official endorsement.
