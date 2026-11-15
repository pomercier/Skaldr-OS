"""Ensure installed Calamares Btrfs partition detection does not depend on blkid.

These read-only tests create sparse GPT-geometry images. They deliberately
exercise filesystem signature offsets, not device nodes or real disks.
"""
from copy import deepcopy
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts/skaldr-find-btrfs-partition.py"
ROLLBACK = ROOT / "scripts/skaldr-ci-installed-rollback.sh"
BTRFS = runpy.run_path(str(HELPER), run_name="test_module")


class InstalledBtrfsPartitionDiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic-raw.img"
        with self.path.open("wb") as f:
            f.truncate(32 * 1024 * 1024)
        self.layout = {
            "partitiontable": {
                "label": "gpt", "sectorsize": 512,
                "partitions": [
                    {"start": 2048, "size": 2048, "type": "efi"},
                    {"start": 4096, "size": 32768, "type": "linux"},
                ],
            }
        }

    def magic_at(self, index):
        part = self.layout["partitiontable"]["partitions"][index]
        with self.path.open("r+b") as f:
            f.seek(part["start"] * 512 + 0x10040)
            f.write(b"_BHRfS_M")

    def test_only_btrfs_partition_is_selected_from_raw_gpt(self):
        self.magic_at(1)
        pick = BTRFS["select_root"](self.path, self.layout)
        self.assertEqual(pick, (4096 * 512, 32768 * 512))

    def test_no_signature_is_an_error_not_a_guess(self):
        with self.assertRaisesRegex(ValueError, "found 0"):
            BTRFS["select_root"](self.path, self.layout)

    def test_two_btrfs_signatures_are_rejected(self):
        self.magic_at(0)
        self.magic_at(1)
        with self.assertRaisesRegex(ValueError, "found 2"):
            BTRFS["select_root"](self.path, self.layout)

    def test_corrupt_gpt_ranges_and_types_are_rejected(self):
        self.magic_at(1)
        for bad in [
            {"label": "dos"},
            {"sectorsize": 1234},
            {"partitions": []},
        ]:
            with self.subTest(bad=bad):
                layout = deepcopy(self.layout)
                layout["partitiontable"].update(bad)
                with self.assertRaises(ValueError):
                    BTRFS["select_root"](self.path, layout)
        layout = deepcopy(self.layout)
        layout["partitiontable"]["partitions"][1]["size"] = 2**48
        with self.assertRaisesRegex(ValueError, "extends beyond"):
            BTRFS["select_root"](self.path, layout)

    def test_symlink_or_nonregular_device_is_rejected(self):
        link = Path(self.tmp.name) / "link.img"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(ValueError, "non-regular or symlinked"):
            BTRFS["select_root"](link, self.layout)
        with self.assertRaisesRegex(ValueError, "non-regular or symlinked"):
            BTRFS["select_root"](Path(self.tmp.name), self.layout)

    def test_cli_requires_exactly_one_signature_and_returns_byte_bounds(self):
        import json
        self.magic_at(1)
        run = subprocess.run(
            [sys.executable, str(HELPER), str(self.path)],
            input=json.dumps(self.layout), capture_output=True, text=True,
            check=False, timeout=10,
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), str(4096 * 512) + " " + str(32768 * 512))

    def test_rollback_uses_read_only_raw_probe_and_separate_real_mount(self):
        code = ROLLBACK.read_text()
        self.assertIn('sfdisk --json "$raw"', code)
        self.assertIn('python3 scripts/skaldr-find-btrfs-partition.py "$raw"', code)
        self.assertIn('losetup --find --show --offset "$offset" --sizelimit "$length" "$raw"', code)
        self.assertIn('mount -t btrfs -o subvolid=5 "$loopdev" "$top"', code)
        self.assertNotIn('blkid -s TYPE -o value "$candidate"', code)
        self.assertIn('Expected exactly one installed Btrfs partition', code)
        self.assertIn('qemu-img check "$restored"', code)


if __name__ == "__main__":
    unittest.main()
