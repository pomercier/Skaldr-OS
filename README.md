<p align="center">
  <img src="assets/skaldr-logo.png" alt="Skaldr OS — Nordic raven emblem" width="190">
</p>

<h1 align="center">Skaldr OS</h1>

<p align="center"><strong>Performance by intention. Freedom by design.</strong></p>

<p align="center">
  An independent, CachyOS-based Linux desktop — created as a personal project and shared openly in case it helps someone else.
</p>

<p align="center">
  <a href="https://github.com/pomercier/Skaldr-OS/actions/workflows/skaldr-checks.yml"><img alt="Source checks" src="https://github.com/pomercier/Skaldr-OS/actions/workflows/skaldr-checks.yml/badge.svg"></a>
  <a href="https://github.com/pomercier/Skaldr-OS/actions/workflows/build.yml"><img alt="ISO build" src="https://github.com/pomercier/Skaldr-OS/actions/workflows/build.yml/badge.svg"></a>
  <img alt="Development release" src="https://img.shields.io/badge/release-0.1.0--dev-blue">
  <img alt="Architecture x86-64" src="https://img.shields.io/badge/architecture-x86__64-5a6881">
</p>

<p align="center">
  <a href="#why-skaldr">Why Skaldr?</a> ·
  <a href="#the-desktop">The desktop</a> ·
  <a href="#versions-you-can-trace">Versioning</a> ·
  <a href="#build-it-yourself">Build</a> ·
  <a href="#project-status">Project status</a>
</p>

---

## A desktop built around the things that matter

Skaldr OS grew from a simple idea: **build the Linux system I actually want to use every day** — fast, flexible, comfortable for gaming and development, and maintainable without rebuilding everything from scratch.

It is built on the work of **[CachyOS](https://cachyos.org/)** and **[Arch Linux](https://archlinux.org/)**. The goal isn't to pretend to replace these projects. It is to add an opinionated, cohesive desktop experience while preserving broad hardware compatibility and upstream improvements.

> **Development preview, not a finished release.** On November 13, 2026, the latest development ISO passed automated UEFI virtual-machine installation, cold boot, KDE login and Skaldr first-run tests with both GRUB/ext4 and Limine/Btrfs. Physical hardware, legacy BIOS and long-term recovery tests remain necessary. Do not rely on a development ISO as your only computer.

## Why Skaldr?

| Built to feel fast | Ready to do more | Hardware-aware |
| :--- | :--- | :--- |
| CachyOS foundations, a preferred `scx_lavd` Gaming profile, performance mode, and ZRAM support. | KDE Plasma, gaming tools, media applications, creative tools, native development and QEMU/KVM. | Detect NVIDIA, AMD, Intel and hybrid graphics; ask before making driver changes. |

| Your everyday workspace | Recover when necessary | No mystery builds |
| :--- | :--- | :--- |
| Brave, LibreOffice Fresh, `yay`, `kcalc`, CMake, Make, fakeroot and other practical utilities. | Btrfs snapshots when applicable, recovery boot options and diagnostic tools. | Each developer ISO records its Skaldr change count, Git revision and UTC build date. |

### What Skaldr deliberately avoids

No mandatory NVIDIA, AMD or Intel driver. No automatic GPU overclock. No Flatpak, Snap or Docker in the default distribution. No forced passwordless `sudo` or insecure installed-system login. No rebranding that hides the upstream work.

The preference for permanent performance settings is intentional, but compatibility checks and recovery paths must take precedence over a system that fails to boot.

## The desktop

**KDE Plasma comes first; other upstream desktop choices remain available.** Skaldr favors a clean desktop with NumLock enabled, normal authentication preserved, and a native toolbox for checking system health, GPU drivers and performance settings.

- **Gaming:** Steam, GameMode, MangoHud, Gamescope and compatibility tools are part of the current package selection.
- **Multimedia and work:** VLC, FFmpeg, LibreOffice Fresh, Brave and other native utilities.
- **Development:** Git, Python, Rust, CMake, Make, Ninja, fakeroot, yay and related tools.
- **Virtualization:** QEMU/KVM and Virt-Manager, when the hardware supports them.
- **Graphics:** CachyOS `chwd` discovers applicable drivers; a first-boot assistant asks before installing them. LACT is available only where supported.
- **Recovery and diagnostics:** Snapper integration on Btrfs, `skaldr-doctor` and the initial KDE control center.

**Performance/security choice:** the requested `mitigations=off` kernel option is currently used for normal boot entries. It disables some CPU security mitigations and is not appropriate for every threat model. A fallback boot entry without this setting is retained.

## Versions you can trace

A rolling-release base can change every day, but **Skaldr's own release number should still mean something**.

Development builds use:

```text
Skaldr OS 0.1.0-dev.N+gSHA
```

Here `N` counts first-parent commits since the original CachyOS fork point; `SHA` identifies the exact source revision. The UTC build date and full 40-character SHA are recorded in the installed build metadata. Upstream CachyOS history is not incorrectly counted as Skaldr development.

On first login, a welcome screen shows this version and build provenance. Later, the same facts are available from:

```bash
skaldr-version
skaldr-version --json
skaldr-doctor --json
```

A stable version such as `v0.1.0` is reserved for a **tested and published release**, never granted simply because a commit was pushed. See [the versioning policy](docs/VERSIONING.md).

## Build it yourself

Skaldr is currently a source-first project. Building its ISO requires a supported Arch/CachyOS environment, sufficient disk space, and access to the package mirrors.

```bash
sudo pacman -Syu --needed archiso mkinitcpio-archiso git squashfs-tools grub
git clone https://github.com/pomercier/Skaldr-OS.git
cd Skaldr-OS
./buildiso.sh -h
sudo ./buildiso.sh -p desktop -v -w
```

The expected output is in `out/desktop/`. The build includes a version manifest and generates SHA-256 checksums. **Do not assume the generated image is installable until its build and VM tests pass.** You can follow the [ISO build workflow](https://github.com/pomercier/Skaldr-OS/actions/workflows/build.yml).

## Download and verify a development image

The successful [Desktop ISO workflow for commit a2203235](https://github.com/pomercier/Skaldr-OS/actions/runs/43367190468) contains the installable developer ISO and its SHA-256 manifest as GitHub Actions artifacts. GitHub Actions artifacts have limited retention and may require a signed-in account.

For future **manually authorized preview releases**, GitHub's per-asset limit is under 2 GiB, so the approximately 4 GiB ISO is split into ordered files named `.iso.part001`, `.iso.part002` and so on. Download every part, `SHA256SUMS`, `SHA256SUMS.parts`, and `reassemble-skaldr-iso.py` to the same folder. Rebuild and verify the original image with:

```text
python3 reassemble-skaldr-iso.py reassemble --directory .
```

The utility refuses missing, modified or unexpected parts and checks the complete ISO's original SHA-256 checksum before making it available. The full-size ISO round trip is also required in the Desktop ISO CI after all three boot scenarios pass. **Never flash an individual part.** See `ASSEMBLE.txt` included with any preview release. No stable release is published automatically.

## Project status

| Area | Current state |
| --- | --- |
| Base | Public CachyOS Live ISO fork, upstream-compatible |
| KDE and software profile | Defined in the Live and target manifests |
| Driver selection | Hardware-aware assistant implemented; real-device matrix still required |
| Performance and Btrfs policies | Initial implementation; platform testing ongoing |
| Version provenance | Implemented in build tooling and first-login welcome |
| CI source validation | Automated on `master` |
| Full ISO build and Calamares installation | **Passed** automated UEFI VM installation, cold boot without the live ISO, password-protected KDE login and first-run Skaldr welcome, for both GRUB/ext4 and Limine/Btrfs ([2026-11-13, run 43465976353](https://github.com/pomercier/Skaldr-OS/actions/runs/43465976353)); **legacy BIOS live boot also passed** in the same workflow; physical hardware and legacy BIOS installation remain untested |
| Wallpaper, final boot splash and hardware certification | Work in progress |

The project's priorities, remaining work and known validation gaps are tracked in [the development roadmap](docs/ROADMAP.md).

## Built personally. Shared publicly.

Skaldr OS is **a personal passion project**, not a business, not a paid product, and not a promise to support every possible device forever.

If the configuration helps another Linux user, that is already a good reason to keep the source public. Contributions and thoughtful bug reports may help improve it over time. Reproducible reports should include the version from `skaldr-version`, hardware details and relevant logs — not passwords or private files.

A future mention on [DistroWatch](https://distrowatch.com/) would be a pleasant milestone, **not a requirement or a measure of success**. The software should earn that attention by being useful, honest and consistently maintained.

## Credits

This project stands on the work of **CachyOS**, **Arch Linux**, the **KDE** community, **Calamares** and the many developers behind the included free and open-source packages. Skaldr OS is **not an official CachyOS project or endorsed edition**.

The original authorship, licenses and credits of upstream files are retained. See [LICENSE](LICENSE).

<p align="center"><em>Make it fast. Keep it usable. Share what works.</em></p>
