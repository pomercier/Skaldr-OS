"""Ensure first-login assertions target unique, reliably OCR-read provenance.

The 2026-11-14 GitHub Action's installed-system screenshots for both GRUB/ext4
and Limine/Btrfs contained the two exact body phrases in 27 frames per VM,
while the full window title was misread. Keep checks for password login and
cold boot; never weaken them to desktop presence alone.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
QT = ROOT / "testcases/cachyos/dailylive/test_install_calamares"
WELCOME = ROOT / "archiso/airootfs/usr/local/bin/skaldr-welcome"


class InstalledWelcomeOCRRegressionTests(unittest.TestCase):
    def test_unique_markers_match_real_welcome_source(self):
        script = QT.read_text(encoding="utf-8")
        app = WELCOME.read_text(encoding="utf-8")
        first_login = script.split("function test_installed_plasma_first_login() {", 1)[1]
        first_login = first_login.split("\nfunction ", 1)[0]
        self.assertIn('qt_send_string_return "$test_password"', first_login)
        for label in ("Skaldr changes since the fork", "Source revision:"):
            self.assertIn(label, first_login)
            self.assertIn(label, app)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Welcome to Skaldr OS"', first_login)

    def test_cold_boot_and_authenticated_kde_login_stay_mandatory(self):
        script = QT.read_text(encoding="utf-8")
        self.assertIn('Second boot still has live installer ISO attached', script)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Show On-Screen Keyboard" 30 10', script)
        self.assertIn('test_installed_system_cold_boot\n    test_installed_plasma_first_login', script)
        self.assertIn('qt_send_string_return "$test_password"', script)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Source revision:" 10 5', script)


if __name__ == "__main__":
    unittest.main()
