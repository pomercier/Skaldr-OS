"""Regression checks for Skaldr's KDE-only branding and release defaults."""
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import yaml

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "archiso/airootfs"
PREPARE = ROOT / "usr/local/bin/skaldr-cal-config"


def write(root, path, text):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    return target


class CalamaresBrandingChecks(unittest.TestCase):
    def make_fixture(self, root, broken=False):
        original = """---
instances:
- id: desktop
  module: packagechooser
  config: packagechooser_desktop.conf
sequence:
- show:
  - welcome@online
  - packagechooser@desktop
  - netinstall
branding: cachyos
"""
        write(root, "usr/share/calamares/settings_online.conf", original)
        write(root, "etc/calamares/settings.conf", original)
        write(root, "etc/calamares/modules/netinstall.yaml", """---
- name: "CachyOS required (hidden)"
  hidden: true
  selected: true
  packages:
    - cachyos-keyring
- name: "CachyOS Packages"
  selected: true
  description: "needed CachyOS packages"
  packages:
    - cachyos-hello
    - cachyos-wallpapers
    - cachyos-settings
- name: "Base-devel + Common packages"
  selected: true
  packages:
    - networkmanager
- name: "KDE-Desktop"
  selected: false
  critical: true
  packages:
    - plasma-desktop
- name: "GNOME-Desktop"
  selected: false
  packages:
    - gnome-shell
- name: "Xfce4"
  selected: false
  packages:
    - xfce4
""")
        write(root, "etc/calamares/modules/netinstall.conf",
              "groupsUrl:\n - https://example.invalid\n")
        write(root, "etc/calamares/modules/packagechooser_desktop.conf",
              "default: KDE-Desktop\n")
        if not broken:
            write(root, "etc/calamares/modules/welcome_online.conf",
                  "requirements:\n    internetCheckUrl: https://wiki.cachyos.org\n")
        write(root, "usr/share/pixmaps/skaldr-logo.png", "mock-logo")
        write(root, "usr/share/wallpapers/Skaldr/contents/images/3840x2160.svg",
              "<svg xmlns='http://www.w3.org/2000/svg' width='3840' height='2160'/>")
        brand = REPO / "archiso/airootfs/usr/share/skaldr/installer"
        for source in brand.iterdir():
            target = root / "usr/share/skaldr/installer" / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)

    def invoke(self, root):
        return subprocess.run([sys.executable, str(PREPARE), "--root", str(root)],
                              capture_output=True, text=True, check=False)

    def test_keeps_only_kde_and_stops_upstream_log_upload(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            result = self.invoke(root)
            self.assertEqual(result.returncode, 0, result.stderr)
            config = yaml.safe_load(
                (root / "etc/calamares/settings.conf").read_text())
            self.assertEqual(config["branding"], "skaldr")
            chooser = yaml.safe_load(
                (root / "etc/calamares/modules/packagechooser_desktop.conf").read_text())
            self.assertEqual(chooser["default"], "KDE-Desktop")
            self.assertEqual([x["id"] for x in chooser["items"]], ["KDE-Desktop"])
            groups = yaml.safe_load(
                (root / "etc/calamares/modules/netinstall.yaml").read_text())
            names = [x["name"] for x in groups]
            self.assertIn("KDE-Desktop", names)
            self.assertNotIn("GNOME-Desktop", names)
            self.assertNotIn("Xfce4", names)
            self.assertTrue(next(x for x in groups if x["name"] == "KDE-Desktop")["selected"])
            base = next(x for x in groups if x["name"] == "Skaldr OS base packages")
            self.assertNotIn("cachyos-hello", base["packages"])
            self.assertNotIn("cachyos-wallpapers", base["packages"])
            self.assertIn("cachyos-settings", base["packages"])
            netinstall = (root / "etc/calamares/modules/netinstall.conf").read_text()
            self.assertNotIn("https://", netinstall)
            branding = yaml.safe_load(
                (root / "usr/share/calamares/branding/skaldr/branding.desc").read_text())
            self.assertEqual(branding["strings"]["productName"], "Skaldr OS")
            self.assertEqual(branding["uploadServer"]["type"], "none")
            self.assertTrue((root / "usr/share/calamares/branding/skaldr/welcome.svg").is_file())
            before = (root / "etc/calamares/modules/netinstall.yaml").read_bytes()
            second = self.invoke(root)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual((root / "etc/calamares/modules/netinstall.yaml").read_bytes(),
                             before)

    def test_missing_calamares_file_fails_without_mutating_installer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root, broken=True)
            conf = root / "etc/calamares/settings.conf"
            original = conf.read_bytes()
            result = self.invoke(root)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(conf.read_bytes(), original)

    def test_vector_wallpapers_and_boot_splashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            logo = root / "usr/share/pixmaps/skaldr-logo.png"
            logo.parent.mkdir(parents=True)
            shutil.copyfile(REPO / "assets/skaldr-logo.png", logo)
            script = REPO / "scripts/skaldr-make-wallpaper.sh"
            result = subprocess.run(["bash", str(script), str(root)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            for resolution in ("3840x2160", "5120x2160"):
                image = root / f"usr/share/wallpapers/Skaldr/contents/images/{resolution}.svg"
                self.assertTrue(image.is_file())
                document = ET.parse(image)
                self.assertEqual(document.getroot().attrib["width"],
                                 resolution.split("x")[0])
                self.assertNotIn("data:image/png", image.read_text())
            boot = subprocess.run([sys.executable,
                                   str(REPO / "scripts/skaldr-make-boot-splash.py"),
                                   str(root)], capture_output=True, text=True)
            self.assertEqual(boot.returncode, 0, boot.stderr)
            for filename in ("grub/splash.png", "syslinux/splash.png", "syslinux/splash1.png"):
                data = (root / filename).read_bytes()
                self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
                self.assertEqual(struct.unpack(">II", data[16:24]), (640, 480))

    def test_visible_boot_entries_are_skaldr_branded(self):
        for filename in (
            "archiso/grub/grub.cfg",
            "archiso/grub/loopback.cfg",
            "archiso/syslinux/archiso_sys-linux.cfg",
            "archiso/syslinux/archiso_pxe-linux.cfg",
            "archiso/efiboot/loader/entries/01-archiso-linux.conf",
            "archiso/efiboot/loader/entries/02-archiso-linux-cachyos.conf",
            "archiso/efiboot/loader/entries/fallback.conf",
        ):
            with self.subTest(filename=filename):
                source = (REPO / filename).read_text()
                self.assertNotIn("Welcome to CachyOS", source)
                self.assertNotIn("MENU LABEL CachyOS", source)
                self.assertNotIn("title   CachyOS", source)
        self.assertIn('PRETTY_NAME="Skaldr OS"',
                      (ROOT / "etc/os-release").read_text())

    def test_artcraft_bundled_with_pinned_hash_and_no_web_fallback(self):
        stage = (REPO / "scripts/skaldr-stage-artcraft.sh").read_text()
        self.assertIn("64197858d155f447ae323f905015116d848f1375675d731eb08d5708f8722e9b",
                      stage)
        self.assertIn("sha256sum --check --status", stage)
        launch = (ROOT / "usr/local/bin/skaldr-artcraft").read_text()
        self.assertIn('exec "$app" "$@"', launch)
        self.assertNotIn("xdg-open", launch)
        self.assertNotIn("releases", launch)
        injected = (ROOT / "usr/local/bin/skaldr-cal-inject").read_text()
        self.assertIn("/opt/skaldr/artcraft/artcraft-launcher.AppImage", injected)
        builder = (REPO / "util-iso.sh").read_text()
        self.assertIn("skaldr-stage-artcraft.sh", builder)
        self.assertIn("skaldr-make-boot-splash.py", builder)


if __name__ == "__main__":
    unittest.main()
