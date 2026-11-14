"""Fail-closed policy tests for the native Qt6 Skaldr Control Center."""
import ast
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIVE = ROOT / "archiso/airootfs"
POLICY_FILE = LIVE / "usr/local/lib/skaldr/control_center_actions.py"
GUI_FILE = LIVE / "usr/local/bin/skaldr-control-center"
WRAPPER = LIVE / "usr/local/bin/skaldr-center"
LEGACY = LIVE / "usr/local/bin/skaldr-center-legacy"


class NativeControlCenterTests(unittest.TestCase):
    def setUp(self):
        self.policy = runpy.run_path(str(POLICY_FILE), run_name="test_policy")

    def test_profile_mutation_requires_opt_in_and_allowlisted_mode(self):
        f = self.policy["power_mode_command"]
        for mode in ("balanced", "gaming", "creator"):
            with self.subTest(mode=mode):
                with self.assertRaises(PermissionError):
                    f(mode)
                self.assertEqual(f(mode, approved=True),
                                 ["konsole", "--hold", "-e", "pkexec",
                                  "/usr/local/bin/skaldr-performance",
                                  "apply", mode, "--confirm"])
        with self.assertRaises(ValueError):
            f("untrusted;rm -rf /", approved=True)

    def test_gui_update_never_offers_unprotected_root_upgrade(self):
        f = self.policy["update_command"]
        for fs in ("ext4", "xfs", "zfs", "unknown", None):
            with self.subTest(fs=fs), self.assertRaises(ValueError):
                f(fs, approved=True)
        with self.assertRaises(PermissionError):
            f("btrfs")
        self.assertEqual(f("btrfs", approved=True),
                         ["konsole", "--hold", "-e", "pkexec",
                          "/usr/local/bin/skaldr-update", "--apply"])

    def test_report_path_is_local_new_and_never_overwritten(self):
        f = self.policy["report_command"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "new.json"
            self.assertEqual(f(path),
                             ["/usr/local/bin/skaldr-report", "--write", str(path)])
            path.write_text("confidential")
            with self.assertRaises(FileExistsError):
                f(path)
            link = Path(tmp) / "sym.json"
            link.symlink_to(path)
            with self.assertRaises(FileExistsError):
                f(link)
            with self.assertRaises(ValueError):
                f("relative.json")

    def test_external_apps_allowlist_does_not_execute_commands(self):
        f = self.policy["get_external_tool"]
        with patch("shutil.which", return_value="/usr/bin/systemsettings"):
            self.assertEqual(f("systemsettings"), ["systemsettings"])
        with self.assertRaises(KeyError):
            f("arbitrary-shell-command")

    def test_dashboard_script_compiles_without_pyside_installed_in_source_ci(self):
        source = GUI_FILE.read_text()
        ast.parse(source)
        self.assertIn("from PySide6.QtWidgets import", source)
        self.assertIn("QStackedWidget", source)
        self.assertIn("QProcess.startDetached", source)
        self.assertIn("QMessageBox.question", source)
        self.assertIn("no network upload", source)
        self.assertNotIn("shell=True", source)
        self.assertNotIn("os.system(", source)
        self.assertIn('--smoke-test', source)

    def test_fallback_preserves_existing_kde_actions(self):
        wrapper = WRAPPER.read_text()
        legacy = LEGACY.read_text()
        self.assertIn("from PySide6 import QtWidgets", wrapper)
        self.assertIn("/usr/local/bin/skaldr-center-legacy", wrapper)
        self.assertIn("SKALDR_CENTER_LEGACY", wrapper)
        self.assertIn("kdialog --title 'Skaldr OS Control Center'", legacy)
        self.assertIn("pkexec /usr/local/bin/skaldr-update --apply", legacy)

    def test_installer_has_python_bindings_and_all_three_app_parts(self):
        live_manifest = (ROOT / "archiso/packages_desktop.x86_64").read_text()
        self.assertIn("\npyside6\n", "\n" + live_manifest)
        installer = (LIVE / "usr/local/bin/skaldr-cal-inject").read_text()
        permissions = (ROOT / "archiso/profiledef.sh").read_text()
        paths = ["/usr/local/bin/skaldr-center",
                 "/usr/local/bin/skaldr-center-legacy",
                 "/usr/local/bin/skaldr-control-center",
                 "/usr/local/lib/skaldr/control_center_actions.py"]
        for item in paths:
            with self.subTest(item=item):
                self.assertIn(f'"{item}"', installer)
                self.assertIn(f'["{item}"]=', permissions)
        config = (LIVE / "usr/local/bin/skaldr-cal-config").read_text()
        self.assertIn('- pyside6', config)
        self.assertIn("Missing KDE packages in netinstall", config)

    def test_arch_source_build_contains_offscreen_qt_smoke(self):
        build = (ROOT / ".github/workflows/build.yml").read_text()
        self.assertIn("QT_QPA_PLATFORM=offscreen", build)
        self.assertIn("skaldr-control-center --smoke-test", build)
        self.assertIn("pacman -S --noconfirm --needed pyside6", build)


if __name__ == "__main__":
    unittest.main()
