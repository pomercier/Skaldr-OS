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
  <a href="https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1"><img alt="Public development preview" src="https://img.shields.io/badge/release-v0.1.0--preview.1-orange"></a>
  <img alt="Architecture x86-64" src="https://img.shields.io/badge/architecture-x86__64-5a6881">
</p>

<p align="center">
  <a href="#download-and-verify-the-public-preview">Download</a> ·
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

> **The first public development preview is available.** [Get v0.1.0-preview.1](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1) (November 13, 2026). Its ISO passed real automated UEFI installations, cold boots, password-protected KDE logins, first-run welcome and legacy BIOS live-boot tests. Physical GPU compatibility, legacy BIOS installation and full recovery tests remain unverified. **Not yet a hardware-certified stable release.**

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

**KDE Plasma is the only desktop environment offered by Skaldr OS.** Other environments can be installed manually later using the Arch package manager. Skaldr favors a clean desktop with NumLock enabled, normal authentication preserved, and a native toolbox for checking system health, GPU drivers and performance settings.

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

The `v0.1.0-preview.1` tag identifies a specific tested development image; its embedded build version remains `0.1.0-dev.62`. A stable `v0.1.0` still requires physical-hardware and recovery validation. See [the versioning policy](docs/VERSIONING.md).

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

## Download and verify the public preview

**[Skaldr OS v0.1.0-preview.1 — seven release files](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1)**

This November 13, 2026 preview contains a validated 4.14 GB ISO, based on
[commit b391fc35](https://github.com/pomercier/Skaldr-OS/commit/b391fc35f4eaade3c1ff5231c33c10f63770bda6).
It passed [source checks](https://github.com/pomercier/Skaldr-OS/actions/runs/43507232909)
and [five ISO validation jobs](https://github.com/pomercier/Skaldr-OS/actions/runs/43507233020).

Download every asset into the **same folder**: three pieces named
`skaldr-0.1.0-dev.62-x86_64.iso.part001`, `.part002`, `.part003`;
`SHA256SUMS`, `SHA256SUMS.parts`, `reassemble-skaldr-iso.py`, and `ASSEMBLE.txt`.
The ISO is split to respect GitHub Releases' per-file size limit.

Run from that folder with Python 3 installed:

```sh
python3 reassemble-skaldr-iso.py reassemble --directory .
```

Use `py` instead of `python3` on Windows if appropriate. The utility verifies
each part and the original complete ISO **before** making it available.
Expected final ISO SHA-256:

```text
b553c0e4cfe01e1de0c857f1dc4c70ac89d41a762bdb01750c770bb77069ec49
```

**Flash only the verified `.iso`, never an individual part.** Use a spare drive
or non-production test machine and read the
[physical-hardware test checklist](docs/HARDWARE-TESTING.md).
All seven release assets were uploaded and their three published part digests
match the CI manifests. Independent reassembly from freshly downloaded
release assets on a second machine is still pending.

## Project status

| Area | Current state |
| --- | --- |
| Base | Public CachyOS Live ISO fork, upstream-compatible |
| KDE and software profile | Defined in the Live and target manifests |
| Driver selection | Hardware-aware assistant implemented; real-device matrix still required |
| Performance and Btrfs policies | Initial implementation; platform testing ongoing |
| Version provenance | Implemented in build tooling and first-login welcome |
| CI source validation | Automated on `master` |
| Public preview | **Published** [v0.1.0-preview.1](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1), seven verified-release assets from `b391fc35` |
| Full ISO build and Calamares installation | **Passed** UEFI GRUB/ext4 and Limine/Btrfs VM installation, cold reboot without the ISO, password-protected KDE login, and first-run Skaldr welcome ([2026-11-13, run 43507233020](https://github.com/pomercier/Skaldr-OS/actions/runs/43507233020)). Legacy BIOS **live boot** passed; physical hardware and legacy BIOS **installation** remain untested |
| Wallpaper, final boot splash and hardware certification | Work in progress |

The project's priorities and gaps are tracked in [the development roadmap](docs/ROADMAP.md). The [hardware test checklist](docs/HARDWARE-TESTING.md) describes what must still be verified.

## Built personally. Shared publicly.

Skaldr OS is **a personal passion project**, not a business, not a paid product, and not a promise to support every possible device forever.

If the configuration helps another Linux user, that is already a good reason to keep the source public. Contributions and thoughtful bug reports may help improve it over time. Reproducible reports should include the version from `skaldr-version`, hardware details and relevant logs — not passwords or private files.

A future mention on [DistroWatch](https://distrowatch.com/) would be a pleasant milestone, **not a requirement or a measure of success**. The software should earn that attention by being useful, honest and consistently maintained.

## Credits

This project stands on the work of **CachyOS**, **Arch Linux**, the **KDE** community, **Calamares** and the many developers behind the included free and open-source packages. Skaldr OS is **not an official CachyOS project or endorsed edition**.

The original authorship, licenses and credits of upstream files are retained. See [LICENSE](LICENSE).

<p align="center"><em>Make it fast. Keep it usable. Share what works.</em></p>
