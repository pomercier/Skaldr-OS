# Skaldr OS — safe controls and recovery (development implementation)

These optional controls are **not** a substitute for physical-hardware and
bootloader recovery testing. They preserve the existing installed-system
password and polkit authorization policy.

## Updates with an explicit Btrfs snapshot

For Btrfs installations with a configured root Snapper profile:

```sh
skaldr-update --dry-run
sudo skaldr-update --apply
```

Before starting `pacman -Syu`, the updater verifies Snapper's root
configuration and creates a **single, timestamped snapshot**. If this fails,
the update stops **before pacman runs**. Pacman's normal interactive questions
and signature verification are preserved, and no automatic rollback is
promised. Btrfs rollback remains a separate recovery procedure.

On ext4/XFS/ZFS the tool refuses to update by default because it cannot
provide a Btrfs snapshot. To explicitly bypass that protection, after verifying
independent backups, use:

```sh
skaldr-update --dry-run --allow-without-snapshot
sudo skaldr-update --apply --allow-without-snapshot
```

Use the Control Center's **Safely update packages** action for Btrfs systems;
other filesystems require the explicit terminal override above.

## Power profiles

```sh
skaldr-performance status
skaldr-performance plan gaming
skaldr-performance plan balanced
skaldr-performance plan creator
sudo skaldr-performance apply balanced --confirm
```

Mode behavior:

| Mode | Power Profiles Daemon | Scheduler / GPU |
|---|---|---|
| `gaming` (default) | `performance` | Retains the existing `scx_lavd` Gaming policy; no overclock |
| `balanced` | `balanced` | Leaves the scheduler configuration untouched; no driver change |
| `creator` | `performance` | Leaves the scheduler configuration untouched; no overclock |

The current version supports **persistent power-mode selection**. It does
*not* yet dynamically switch the sched_ext scheduler for each profile or claim
different benchmark results for Creator vs Gaming. The selected mode is stored
in `/etc/skaldr/performance-profile`, and the existing systemd performance
service re-applies its power choice on reboot. Unavailable power profiles
fail without persisting the change. Roll back by choosing `gaming`.

## Local, privacy-limited diagnostics

```sh
skaldr-report
skaldr-report --write ~/skaldr-diagnostic.json
```

This calls `skaldr-doctor --json` but exports only an explicit allowlist of
operating-system, performance and GPU *device descriptions*. It does not
automatically export account names, network addresses, environment variables,
serial numbers, full PCI inventory, Wi-Fi details or Calamares logs. Files
are created with mode `0600`, never overwrite existing files or symlinks,
and are **never uploaded**. The user should still review the content before
sharing with anyone.

## Control Center

The existing KDE `skaldr-center` menu now links to the updater, diagnostics
and three power modes through an explicit consent step. This is an incremental
control-center improvement, **not yet a complete native Qt application**.

## Validation boundary

Automated source tests verify missing-snapshot refusal, root authorization,
profile persistence, no remote upload, non-destructive local file output and
Calamares propagation. Functional real-hardware tests for Snapper rollback,
power modes, graphics and disk recovery are still outstanding.
