"""Read-only recovery diagnosis of explicit Btrfs kernel rootflags."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import runpy

SCRIPT = Path(__file__).resolve().parents[1] / (
    "archiso/airootfs/usr/local/bin/skaldr-recovery"
)
namespace = runpy.run_path(str(SCRIPT))
parse = namespace["root_subvolume_override"]
status = namespace["status"]


class RecoveryBootFlagsTests(TestCase):
    def test_no_override_is_unknown_not_proof_of_safe_rollback(self):
        self.assertIsNone(parse("quiet rootflags=compress=zstd root=UUID=1234"))
        self.assertIsNone(parse(None))

    def test_subvol_override_with_other_mount_options(self):
        self.assertEqual(
            parse("quiet rootflags=subvol=@,compress=zstd:3 root=UUID=1234"),
            "subvol=@",
        )

    def test_subvolid_override_with_quotes(self):
        self.assertEqual(
            parse('rootflags="compress=zstd,subvolid=257" quiet'),
            "subvolid=257",
        )

    def test_last_explicit_override_is_reported(self):
        self.assertEqual(
            parse("rootflags=subvol=@ rootflags=subvol=/@recovered"),
            "subvol=/@recovered",
        )

    def test_unavailable_kernel_cmdline_is_not_misrepresented(self):
        with TemporaryDirectory() as directory:
            with patch.dict(status.__globals__, {"command": lambda *a: None}):
                report = status(Path(directory))
        self.assertFalse(report["kernel_rootflags_checked"])
        self.assertIsNone(report["default_subvolume_change_sufficient_for_boot"])
        self.assertIsNone(report["kernel_root_subvolume_override"])

    def test_override_warns_that_default_switch_is_insufficient(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proc").mkdir()
            (root / "proc/cmdline").write_text(
                "BOOT_IMAGE=/vmlinuz rootflags=subvol=@,compress=zstd quiet",
                encoding="utf-8",
            )
            with patch.dict(status.__globals__, {"command": lambda *a: None}):
                report = status(root)
        self.assertEqual(report["kernel_root_subvolume_override"], "subvol=@")
        self.assertTrue(report["kernel_rootflags_checked"])
        self.assertIs(report["default_subvolume_change_sufficient_for_boot"], False)
        self.assertFalse(report["rollback_verified"])

    def test_absence_of_override_does_not_claim_safe_boot(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "proc").mkdir()
            (root / "proc/cmdline").write_text("root=UUID=1234 quiet")
            with patch.dict(status.__globals__, {"command": lambda *a: None}):
                report = status(root)
        self.assertTrue(report["kernel_rootflags_checked"])
        self.assertIsNone(report["kernel_root_subvolume_override"])
        self.assertIsNone(report["default_subvolume_change_sufficient_for_boot"])
