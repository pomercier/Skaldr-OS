# Skaldr OS — autonomous engineering protocol

These are repository-local instructions for future coding-agent sessions.
They do not grant background execution or permission to claim untested results.

## Objective

Produce a reliable, installable, recoverable KDE Plasma-only distribution
derived from CachyOS. Preserve upstream compatibility, version provenance and
honest descriptions of tested features and current limitations.

## Iterative work cycle

Repeat **analyze → act → test → correct → retest** as many times as
the active session and tools permit.

1. **Analyze:** verify the current `master` head, recent workflow runs and
   failure logs, known regression tests and the highest-priority open blocker.
   Distinguish physical, VM, unit and screenshot evidence.
2. **Act:** make the smallest change that fixes the observed root cause.
   Preserve functionality already demonstrated by earlier tests.
3. **Test:** run focused unit/static checks. For code that changes the live
   ISO, installed system, Calamares, boot, GPU or recovery behavior, require
   the full `Desktop ISO` workflow on the **exact source revision**.
4. **Correct:** inspect actual failing logs and test outputs. Change the
   hypothesis or implementation before repeating an unsuccessful test; do
   not blindly rerun the same job without evidence of an intermittent failure.
5. **Retest:** do not mark a correction complete until its necessary
   verification has passed. Once successful, identify the next highest-impact
   blocker and continue rather than stopping after a single fix.

Never equate queued/running/skipped jobs with passing jobs. Never equate
a VM screenshot with a completed installation, cold reboot or physical GPU
certification. User-provided VM evidence is valuable; record exactly what
the image demonstrates and which installation/boot tests remain unverified.

Minimize progress chatter; report exact commit(s), passing checks, remaining
failures and the next necessary action at the end of each execution. Do not
promise work continuing outside the active session.

## Priorities

- **P0:** successful full ISO build, live boot, real Calamares installation,
  installed KDE login, offline recovery and failure prevention.
- **P1:** physical NVIDIA, AMD and Intel graphics validation, driver consent,
  suspend/resume, repeatable updates, hardware compatibility and privacy.
- **P2:** KDE-only desktop polish, installer/login branding, ArtCraft, guided
  configuration and accessibility.
- **P3:** optional visual features and broader project publicity.

Use [docs/ROADMAP.md](docs/ROADMAP.md),
[docs/HARDWARE-TESTING.md](docs/HARDWARE-TESTING.md) and
[docs/RELEASE-READINESS.md](docs/RELEASE-READINESS.md) to track proof.

## Git policy

- Keep exactly one permanent branch: existing `master`. Do not rename the
  default branch, retain temporary branches, or force-push.
- Write new commit messages, code comments and project documentation in English.
- Preserve upstream CachyOS package identifiers where required for upgrades.
- Detect NVIDIA, AMD and Intel; do not assume a specific proprietary driver.
- Do not remove system passwords, sudo/polkit prompts or authentication.
- Prefer safe fallback paths for sched_ext, graphics, kernel and recovery.
- Do not replace or silently rebuild a previously published release.

## Release policy

The published [v0.1.0-preview.3](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.3)
contains the independently verified `dev.149` ISO, not any later change.
Its original source was `1b4c3d0c4be1b828edbfd3e202e97a13f0ddb89f`.

Stable publishing stays blocked until there is a separately built and tested
release-mode ISO and independently reviewed physical-hardware and recovery
proof, consistent with [RELEASE-EVIDENCE.json](docs/RELEASE-EVIDENCE.json).
Evidence absent from CI or the hardware record remains **untested**.
