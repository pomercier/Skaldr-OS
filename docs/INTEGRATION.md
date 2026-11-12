# Skaldr OS integration checks

This source currently targets x86_64, as does the upstream CachyOS Live ISO.
The latest compatible proprietary GPU driver is offered only if chwd lists
a suitable profile. No driver is changed automatically.

The Calamares target integration uses pacstrap.postInstallFiles and the
shellprocess postinstall step. This integration must be validated with
the exact runtime Calamares package before the ISO is released.

The live ISO and target install use the same package manifest. Desktop
selection remains under Calamares control with KDE as its existing default.
The Caps Lock helper works on X11; Wayland and the login manager need
additional compositor-specific validation.
