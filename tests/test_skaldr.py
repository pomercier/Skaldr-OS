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

    def test_versioning_and_first_login(self):
        version_script = REPO / "scripts/skaldr-version.py"
        self.assertEqual((REPO / "VERSION").read_text().strip(), "0.1.0")
        self.assertIn("FORK_POINT", version_script.read_text())
        result = subprocess.run([sys.executable, str(version_script), "--json"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        import json
        data = json.loads(result.stdout)
        self.assertRegex(data["version"], r"^0\.1\.0-dev\.\d+\+g[0-9a-f]{8}$")
        self.assertGreater(data["project_commit_count"], 0)
        self.assertEqual(len(data["git_revision"]), 40)
        self.assertTrue((LIVE / "usr/local/bin/skaldr-welcome").is_file())
        self.assertIn("welcome-shown", (LIVE / "usr/local/bin/skaldr-welcome").read_text())
        self.assertIn("/usr/share/skaldr/build.json", INJECT.read_text())
        # Verify the exact version is prepared in the staged Live image.
        source = (REPO / "util-iso.sh").read_text()
        self.assertIn("--install-to", source)
        self.assertIn('iso_file="skaldr-', source)
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "usr/share/skaldr/os-release"
            template.parent.mkdir(parents=True)
            template.write_text('NAME="Skaldr OS"\nID=arch\n')
            check = subprocess.run([sys.executable, str(version_script),
                                    "--install-to", tmp],
                                   capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn('VERSION_ID="0.1.0-dev.',
                          (Path(tmp) / "etc/os-release").read_text())
            self.assertEqual(json.loads((Path(tmp) / "usr/share/skaldr/build.json")
                                        .read_text())["git_revision"], data["git_revision"])

    def test_offline_raven_wallpaper(self):
        import shutil
        source_logo = REPO / "assets/skaldr-logo.png"
        self.assertTrue(source_logo.is_file())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            logo = root / "usr/share/pixmaps/skaldr-logo.png"
            logo.parent.mkdir(parents=True)
            shutil.copyfile(source_logo, logo)
            result = subprocess.run(["bash", str(REPO / "scripts/skaldr-make-wallpaper.sh"), str(root)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            wall = root / "usr/share/wallpapers/Skaldr/contents/images/1920x1080.svg"
            self.assertIn("data:image/png;base64,", wall.read_text())
            self.assertIn("Skaldr OS", wall.read_text())
            self.assertNotIn("https://", wall.read_text())
        t = (LIVE / "usr/local/bin/skaldr-theme").read_text()
        self.assertIn("plasma-apply-wallpaperimage", t)
        self.assertIn("wallpaper-applied", t)
        self.assertIn("skaldr-theme.desktop", INJECT.read_text())

    def test_ci_boot_preflight(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text()
        self.assertIn("Install Git before checkout", workflow)
        self.assertIn("pacman -Syu --noconfirm --needed git", workflow)
        self.assertLess(workflow.index("Install Git before checkout"),
                        workflow.index("Checkout complete Skaldr OS repository history"))
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn('git -c "safe.directory=$GITHUB_WORKSPACE" cat-file -e 3215497d2e8c5fea90e185affcf973dfa2cf790b', workflow)
        self.assertIn("python3 scripts/skaldr-version.py --json", workflow)
        self.assertIn("bootloader: grub", workflow)
        self.assertIn("filesystem: btrfs", workflow)
        self.assertIn("filesystem: ext4", workflow)
        qt = (REPO / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Welcome to Skaldr OS!"', qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "$text_calamares_welcome"', qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Launch installer"', qt)
        self.assertIn('mouse="usb"', (REPO / "machines/cachyos-dailylive.conf").read_text())
        self.assertIn('qt_send_command "mouse_move -80 -80"', qt)
        self.assertIn('target_x=$((width * 45 / 100))', qt)
        self.assertIn('target_y=$((height * 74 / 100))', qt)
        self.assertIn('qt_send_command "mouse_button 1"', qt)
        self.assertIn('qt_send_command "mouse_button 0"', qt)
        self.assertNotIn('qt_send_string_return "/usr/local/bin/calamares-online.sh"', qt)
        self.assertNotIn('qt_send_string_tab "CALAMARES_SKIP_GEOIP=1 sudo', qt)
        self.assertIn("qt_wait_for_seconds 90", qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "$text_calamares_welcome" 12 15', qt)

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
