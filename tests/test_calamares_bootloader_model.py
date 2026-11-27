"""Fail-closed tests for Qt model resets and actual Calamares VM summary."""
import runpy
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-patch-calamares-bootloader-model.py"
M = runpy.run_path(str(SCRIPT), run_name="skaldr_patch_test")
SRC = (
    M["INIT_OLD"] + "\n" + M["UPDATE_OLD"] + "\n"
    + "void\nBootLoaderModel::updateInternal()\n{\n    clear();\n    createMbrItems();\n}\n"
)


class CalamaresResetTests(unittest.TestCase):
    def test_removes_nested_resets_not_model_clear(self):
        fixed = M["patch_source"](SRC)
        self.assertIn(M["INIT_NEW"], fixed)
        self.assertIn(M["UPDATE_NEW"], fixed)
        self.assertIn("clear();", fixed)
        self.assertIn("createMbrItems();", fixed)
        self.assertNotIn("beginResetModel();", fixed)
        self.assertNotIn("endResetModel();", fixed)

    def test_changed_upstream_fails_closed(self):
        for invalid in (SRC.replace("beginResetModel();", "", 1),
                        SRC.replace("clear();", "removeRows(0, rowCount());"),
                        SRC + M["UPDATE_OLD"]):
            with self.assertRaises(ValueError):
                M["patch_source"](invalid)

    def test_cli_only_changes_requested_file_and_cannot_repeat_patch(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "BootLoaderModel.cpp"
            p.write_text(SRC)
            a = subprocess.run(["python3", str(SCRIPT), str(p)],
                               capture_output=True, text=True, check=False)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(p.read_text(), M["patch_source"](SRC))
            b = subprocess.run(["python3", str(SCRIPT), str(p)],
                               capture_output=True, text=True, check=False)
            self.assertNotEqual(b.returncode, 0)

    def test_rebuild_quarantines_unverified_qt_reset_patch(self):
        script = ROOT / "scripts/skaldr-build-calamares.sh"
        content = script.read_text()
        self.assertIn("QUARANTINED", content)
        self.assertNotIn("SKALDR_PREPARE_PATCH", content)
        self.assertNotIn('"$work/skaldr-patch-calamares-bootloader-model.py"', content)
        self.assertIn("actual_revision", content)
        proc = subprocess.run(["bash", "-n", str(script)],
                              capture_output=True, text=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_real_vm_ocr_cues_and_disk_only_cold_boot_still_required(self):
        i18n = (ROOT / "testcases/cachyos/dailylive/i18n/en_US").read_text()
        case = (ROOT / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertIn(
            'text_calamares_summary="This is an overview of what will happen"',
            i18n,
        )
        self.assertNotIn('text_calamares_summary="Erase disk /dev/vda"', i18n)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Create new" 5 3', case)
        self.assertIn("test_installed_system_cold_boot", case)
        self.assertIn("test_installed_native_control_center", case)


if __name__ == "__main__":
    unittest.main()
