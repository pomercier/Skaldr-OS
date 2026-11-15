"""Regressions for branded driver guidance and real installed Qt6 UI evidence."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "archiso/airootfs/usr/local/bin/skaldr-gpu-assistant"
QT = ROOT / "testcases/cachyos/dailylive/test_install_calamares"
DOCTOR = ROOT / "archiso/airootfs/usr/local/bin/skaldr-doctor"
UI = ROOT / "archiso/airootfs/usr/local/bin/skaldr-control-center"


class DriverBrandingTests(unittest.TestCase):
    def test_driver_assistant_uses_skaldr_text_but_preserves_chwd_backend(self):
        source = DRIVER.read_text()
        self.assertIn("Skaldr OS can detect compatible drivers", source)
        self.assertIn("Install recommended compatible drivers (default)", source)
        self.assertIn("Allow Skaldr OS to install", source)
        self.assertNotIn("CachyOS will detect", source)
        self.assertNotIn("CachyOS drivers (default)", source)
        self.assertIn('available="$(chwd --list', source)
        self.assertIn("pkexec chwd -a", source)
        self.assertIn("pkexec chwd -i nouveau", source)
        self.assertIn('kdialog --yesno "Allow Skaldr OS', source)
        self.assertIn('kdialog --yesno "Install the available Nouveau profile?', source)

    def test_installed_control_center_checks_populated_real_diagnostics(self):
        source = QT.read_text()
        stage = source.split("function test_installed_native_control_center() {", 1)[1]
        stage = stage.split("\nfunction ", 1)[0]
        # Proven by actual archived OCR text in both 2026-11-14 UEFI VMs:
        # "System overview", "Refresh information", "Kernel:".
        for marker in ("System overview", "Refresh information", "Kernel:"):
            self.assertIn(f'qt_wait_for_text "$FUNCNAME" "{marker}"', stage)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Live system health"', stage)
        self.assertIn('qt_send_string_return "skaldr-center"', stage)
        self.assertIn('qt_screenshot_ppm "$FUNCNAME"', stage)
        self.assertNotIn("pkexec", stage)
        gui = UI.read_text()
        doctor = DOCTOR.read_text()
        self.assertIn("System overview", gui)
        self.assertIn("Refresh information", gui)
        self.assertIn('f"{k.replace(', gui)
        self.assertIn('"kernel"', doctor)


if __name__ == "__main__":
    unittest.main()
