"""Require an actual KDE/Wayland launch of the installed Qt6 Control Center.

This integration stage runs AFTER Calamares, cold boot, password login and
the first-run Skaldr welcome in both UEFI GRUB/ext4 and Limine/Btrfs VMs.
No button with elevated privileges is clicked.
"""
from pathlib import Path
import unittest

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "testcases/cachyos/dailylive/test_install_calamares"
GUI = REPO / "archiso/airootfs/usr/local/bin/skaldr-control-center"
WRAPPER = REPO / "archiso/airootfs/usr/local/bin/skaldr-center"


class NativeInstalledKDEUITests(unittest.TestCase):
    def test_control_center_is_launched_in_real_installed_session(self):
        script = SCRIPT.read_text()
        self.assertIn("function test_installed_native_control_center() {", script)
        stage = script.split("function test_installed_native_control_center() {", 1)[1]
        stage = stage.split("\nfunction ", 1)[0]
        self.assertIn('qt_send_key_combo "alt-f2"', stage)
        self.assertIn('qt_send_string_return "skaldr-center"', stage)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "System overview"', stage)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Live system health"', stage)
        self.assertIn('qt_screenshot_ppm "$FUNCNAME"', stage)
        self.assertNotIn("pkexec", stage)
        self.assertLess(script.index("    test_installed_system_cold_boot\n"),
                        script.index("    test_installed_plasma_first_login\n"))
        self.assertLess(script.index("    test_installed_plasma_first_login\n"),
                        script.index("    test_installed_native_control_center\n"))
        self.assertLess(script.index("    test_installed_native_control_center\n"),
                        script.index("    test_power_off_vm\n"))

    def test_tested_gui_labels_match_installed_native_app(self):
        ui = GUI.read_text()
        for phrase in ("System overview", "Live system health"):
            self.assertIn(phrase, ui)
        self.assertIn("from PySide6.QtWidgets import", ui)
        self.assertIn("/usr/local/bin/skaldr-control-center", WRAPPER.read_text())


if __name__ == "__main__":
    unittest.main()
