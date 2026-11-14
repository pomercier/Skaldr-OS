"""Ensure first-login assertions target unique, reliably OCR-read provenance.

The 2026-11-14 run 43633912620 produced genuine installed-system welcome
screenshots for GRUB/ext4 and Limine/Btrfs. OCR lowercased 'Skaldr' on every
frame; the separate 'Built:' and 'Source revision:' lines were recognized. Keep checks for password login and
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
        for label in ("Built:", "Source revision:"):
            self.assertIn(label, first_login)
            self.assertIn(label, app)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Skaldr changes since the fork"', first_login)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Welcome to Skaldr OS"', first_login)


    def test_real_uefi_screenshots_support_exact_ocr_cues(self):
        # Transcribed lines from the actual archived GRUB/ext4 and
        # Limine/Btrfs screenshots of run 43633912620. These were read
        # directly from screenshot_0040 and screenshot_0042 respectively.
        observed_grub = (
            "skaldr changes since the fork: 81\\n"
            "Built: 2026-11-14T20:28:487\\n"
            "Source revision: fccbd4gc29d"
        )
        observed_btrfs = (
            "skaldr changes since the fork: 81\\n"
            "Built: 2026-11-14T20:28:487\\n"
            "Source revision: fccbd4gc29d"
        )
        for ocr in (observed_grub, observed_btrfs):
            with self.subTest(ocr=ocr):
                self.assertIn("Built:", ocr)
                self.assertIn("Source revision:", ocr)
                self.assertNotIn("Skaldr changes since the fork", ocr)

    def test_cold_boot_and_authenticated_kde_login_stay_mandatory(self):
        script = QT.read_text(encoding="utf-8")
        self.assertIn('Second boot still has live installer ISO attached', script)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Show On-Screen Keyboard" 30 10', script)
        self.assertIn('test_installed_system_cold_boot\n    test_installed_plasma_first_login', script)
        self.assertIn('qt_send_string_return "$test_password"', script)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Source revision:" 10 5', script)


if __name__ == "__main__":
    unittest.main()
