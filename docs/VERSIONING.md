# Skaldr OS release numbering

Skaldr OS is a personal, independent, public CachyOS-based project. Its own
release version tracks **Skaldr customization**, not the Arch package version.

## Developer builds

`0.1.0-dev.N+gSHA`

- `0.1.0`: the next intended public release line (read from root `VERSION`).
- `dev`: clearly marks an unvalidated developer build.
- `N`: number of *first-parent* commits since the fork point
  `3215497d2e8c5fea90e185affcf973dfa2cf790b`. It increases when we
  integrate a fix, feature or upstream merge, but does not count thousands
  of inherited CachyOS commits.
- `gSHA`: first eight characters of the exact source Git commit.
- Build date in UTC is stored **separately** and never replaces the version.

Example (illustrative): `0.1.0-dev.24+g1234abcd`.

The ISO filename uses `skaldr-0.1.0-dev.N-x86_64.iso`.
The full source revision, build date, fork point, architecture and project
change count are embedded in `/usr/share/skaldr/build.json`, and the release
appears in `/etc/skaldr-release` and `/etc/os-release`.

Each installed user sees the full version and short Git revision on their
**first login** via the `skaldr-welcome` dialog. It is also available
through `skaldr-version` or `skaldr-version --json`.

## Validated public releases

The first public **development preview** is [v0.1.0-preview.1](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1), published November 13, 2026 from validated commit `b391fc35f4eaade3c1ff5231c33c10f63770bda6`. Its ISO embeds build version `0.1.0-dev.62`; the public preview tag and internal build number serve different purposes.

Stable `v0.1.0` remains blocked pending real-hardware, recovery and release-mode build validation. A new feature increments MINOR, compatible fixes increment PATCH, and breaking architectural changes can increment MAJOR.

The development counter is a traceability aid, **not a statement that the ISO
has passed installation tests**. A build tag and checksums are linked to an
exact source revision. Never silently replace a published release.

## DistroWatch: optional, not a prerequisite

A DistroWatch mention would be a welcome bonus, not a project KPI. The focus
is a useful desktop distribution and honest public documentation.

Once a stable ISO is independently verified, keep clear release notes, a
download link, checksums, screenshots, support guidance and a concise summary
of what Skaldr changes compared with CachyOS. Do not submit the project as
completed until the software is genuinely installable.
