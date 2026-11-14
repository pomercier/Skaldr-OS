# Skaldr OS integration checks

This source currently targets x86_64, as does the upstream CachyOS Live ISO.
The latest compatible proprietary GPU driver is offered only if chwd lists
a suitable profile. No driver is changed automatically.

The Calamares target integration uses pacstrap.postInstallFiles and the
shellprocess postinstall step. This integration must be validated with
the exact runtime Calamares package before the ISO is released.

The live ISO ships KDE Plasma only, and the installed system uses an
independent local Calamares chooser with KDE Plasma as the only desktop.
Non-KDE upstream choices are excluded from the local netinstall manifest.
Underlying CachyOS package IDs remain unchanged for compatibility.
Skaldr branding and diagnostics do not rely on CachyOS Hello or paste uploads.
The Caps Lock helper works on X11; Wayland and the login manager need
additional compositor-specific validation.

## Scheduler compatibility

Skaldr prefers the scx_lavd Gaming profile via scx_loader. The installed
system includes a systemd condition for /sys/kernel/sched_ext so kernels
without this feature skip scx_loader cleanly, without disabling the default
in-kernel Linux CPU scheduler. On a supported kernel, normal scx_loader
behavior is unchanged. If a sched_ext scheduler later stops or fails, the
kernel reverts to its in-kernel scheduler.

Use `skaldr-doctor --json` to distinguish the daemon's service state,
the current sched_ext state, and the active scheduler. The condition and
report have isolated tests; real hardware failure/recovery tests remain
required before claiming universal compatibility.
