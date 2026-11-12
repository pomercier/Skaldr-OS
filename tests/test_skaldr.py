#!/usr/bin/env python3
"""Static and isolated integration checks for the Skaldr OS ISO sources."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "archiso" / "airootfs"
PROFILE = LIVE / "usr/local/bin/skaldr-profile"
INJECT = LIVE / "usr/local/bin/skaldr-cal-inject"
MANIFEST = LIVE / "usr/share/skaldr/packages.txt"
BOOT = [
    REPO / "archiso/grub/grub.cfg",
    REPO / "archiso/grub/loopback.cfg",
    REPO / "archiso/syslinux/archiso_sys-linux.cfg",
    REPO / "archiso/efiboot/loader/entries/01-archiso-linux.conf",
    REPO / "archiso/efiboot/loader/entries/02-archiso-linux-cachyos.conf",
]
try:
    import yaml
except ImportError:
    yaml = None

class SkaldrChecks(unittest.TestCase):
    def test_packages(self):
        live = (REPO / "archiso/packages_desktop.x86_64").read_text().splitlines()
        installed = [line.strip() for line in MANIFEST.read_text().splitlines() if line.strip()]
        self.assertEqual(len(live), len(set(live)), "Duplicate live packages")
        for package in installed:
            self.assertIn(package, live, "Target-only package: " + package)
        for package in ("brave-bin", "libreoffice-fresh", "libreoffice-fresh-fr",
                        "cmake", "make", "fakeroot", "yay", "kcalc", "lact"):
            self.assertIn(package, live)
        for forbidden in ("firefox", "flatpak", "snapd", "docker", "preload", "prelink"):
            self.assertNotIn(forbidden, live)
            self.assertNotIn(forbidden, installed)

    def test_graphics_are_hardware_neutral(self):
        forbidden = {"linux-cachyos-nvidia-open", "linux-cachyos-lts-nvidia-open",
                     "nvidia-utils", "lib32-vulkan-intel", "lib32-vulkan-radeon"}
        live = set((REPO / "archiso/packages_desktop.x86_64").read_text().splitlines())
        installed = set(MANIFEST.read_text().splitlines())
        for packages in (live, installed):
            self.assertFalse(forbidden & packages)
            for item in ("vulkan-swrast", "lib32-vulkan-swrast",
                         "vulkan-icd-loader", "lib32-vulkan-icd-loader"):
                self.assertIn(item, packages)
        assistant = (LIVE / "usr/local/bin/skaldr-gpu-assistant").read_text()
        self.assertIn("pkexec chwd -a", assistant)
        self.assertNotIn("nvidia-dkms-580xx nvidia-dkms-470xx", assistant)

    def test_numlock_and_installer(self):
        self.assertEqual((LIVE / "etc/xdg/kcminputrc").read_text(), "[Keyboard]\nNumLock=0\n")
        self.assertFalse((LIVE / "etc/skel/.config/kcminputrc").exists())
        self.assertIn("install -m 0644", (LIVE / "usr/local/bin/skaldr-numlock").read_text())
        self.assertFalse((LIVE / "usr/local/bin/skaldr-capslock").exists())
        self.assertFalse((LIVE / "etc/xdg/autostart/skaldr-capslock.desktop").exists())
        self.assertIn("skaldr-numlock", INJECT.read_text())
        installer = (LIVE / "usr/local/bin/calamares-online.sh").read_text()
        self.assertIn("sudo /usr/local/bin/skaldr-cal-inject", installer)
        self.assertNotIn("exit 1\\n", installer)

    def test_branding_and_controls(self):
        release = (LIVE / "etc/os-release").read_text()
        self.assertIn('NAME="Skaldr OS"', release)
        profile = (REPO / "archiso/profiledef.sh").read_text()
        self.assertIn('iso_name="skaldr"', profile)
        self.assertIn("SKALDR_", profile)
        for name in ("skaldr-doctor", "skaldr-center"):
            self.assertTrue((LIVE / "usr/local/bin" / name).is_file())
        injector = INJECT.read_text()
        self.assertIn("/usr/share/skaldr/os-release", injector)
        self.assertIn("/usr/local/bin/skaldr-center", injector)
        cleanup = (LIVE / "usr/local/bin/removeun").read_text()
        self.assertNotIn("pacman -Rsnc", cleanup)

    def test_snapshots_and_thermal_checks(self):
        profile = PROFILE.read_text()
        self.assertIn('fs.stdout.strip() != "btrfs"', profile)
        self.assertIn('"snapper-cleanup.timer"', profile)
        self.assertIn('"snapper-timeline.timer"', profile)
        doctor = (LIVE / "usr/local/bin/skaldr-doctor").read_text()
        self.assertIn('"highest_sensor_temperature_celsius"', doctor)
        for name in ("snapper", "snap-pac", "smartmontools"):
            self.assertIn(name, (REPO / "archiso/packages_desktop.x86_64").read_text().splitlines())

    def test_iso_output_uses_skaldr_name(self):
        script = (REPO / 'util-iso.sh').read_text()
        self.assertIn('vars+=("skaldr")', script)
        self.assertIn('built_iso=', script)
        self.assertNotIn('source "${work_dir}/archiso/profiledef.sh"', script)
        self.assertIn('iso_name="$(sed -n ', script)
        self.assertIn('iso_arch="$(sed -n ', script)
        self.assertNotIn('mv "$outFolder/$_profile/cachyos-', script)
        self.assertNotIn("occt", (REPO / "archiso/packages_desktop.x86_64").read_text().splitlines())

    def test_policy(self):
        profile = PROFILE.read_text()
        self.assertIn('vm.swappiness = 0', profile)
        self.assertIn('default_sched = "scx_lavd"', profile)
        self.assertIn('default_mode = "Gaming"', profile)
        self.assertIn('performance', profile.lower())
        self.assertIn('mitigations=off', profile)
        self.assertIn('os.geteuid()', profile)

    def test_live_boot(self):
        for path in BOOT:
            self.assertIn("mitigations=off", path.read_text(), str(path))
        grub = BOOT[0].read_text()
        fallback = grub.split("menuentry \"Skaldr OS Legacy Hardware")[1].split("menuentry ")[0]
        self.assertNotIn("mitigations=off", fallback, "Emergency fallback must stay usable")

    @unittest.skipIf(yaml is None, "PyYAML is not available")
    def test_calamares_hook(self):
        for with_i18n in (True, False):
            with self.subTest(with_i18n=with_i18n):
                with tempfile.TemporaryDirectory() as d:
                    root = Path(d)
                    pacstrap = root / "pacstrap.conf"
                    process = root / "shellprocess.conf"
                    pacstrap.write_text('---\nbasePackages:\n - base\npostInstallFiles:\n - "/etc/mkinitcpio.conf"\n')
                    suffix = '\ni18n:\n  name: "Cleanup"\n' if with_i18n else ''
                    process.write_text('---\ndontChroot: false\nscript:\n  - command: "/usr/local/bin/dmcheck"\n' + suffix)
                    env = dict(os.environ, SKALDR_CALAMARES_MODULES=d)
                    for _ in range(2):
                        completed = subprocess.run([sys.executable, str(INJECT)],
                            env=env, capture_output=True, text=True)
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                    p = yaml.safe_load(pacstrap.read_text())
                    s = yaml.safe_load(process.read_text())
                    self.assertIn("/usr/local/bin/skaldr-postinstall", p["postInstallFiles"])
                    self.assertIn("/etc/systemd/system/skaldr-performance.service", p["postInstallFiles"])
                    steps = [v.get("command") for v in s["script"] if isinstance(v, dict)]
                    self.assertEqual(steps.count("/usr/local/bin/skaldr-postinstall"), 1)
                    self.assertEqual(steps[0], "/usr/local/bin/dmcheck")

if __name__ == "__main__":
    unittest.main()
