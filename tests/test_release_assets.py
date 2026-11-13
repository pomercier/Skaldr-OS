"""Offline tests for safe large-ISO release splitting and reconstruction."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/skaldr-release-assets.py"
spec = importlib.util.spec_from_file_location("skaldr_release_assets", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReleaseAssetsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.iso = self.root / "skaldr-preview-x86_64.iso"
        self.data = bytes(range(256)) * 3
        self.iso.write_bytes(self.data)
        self.sha = hashlib.sha256(self.data).hexdigest()
        self.sum = self.root / "SHA256SUMS"
        self.sum.write_text(f"{self.sha}  {self.iso.name}\n")
        self.assets = self.root / "release-assets"

    def tearDown(self):
        self.tmp.cleanup()

    def test_prepare_and_reassemble_verified_iso(self):
        parts = module.prepare(self.iso, self.sum, self.assets, part_size=225)
        self.assertEqual(len(parts), 4)
        self.assertTrue(all((self.assets / name).stat().st_size < 2**31 for name, _ in parts))
        self.assertTrue((self.assets / "SHA256SUMS.parts").exists())
        self.assertTrue((self.assets / "reassemble-skaldr-iso.py").exists())
        self.assertTrue((self.assets / "ASSEMBLE.txt").exists())
        result = module.reassemble(self.assets)
        self.assertEqual(result.read_bytes(), self.data)
        self.assertEqual(module.reassemble(self.assets), result)

    def test_bad_source_checksum_rejected(self):
        self.sum.write_text(f"{'0'*64}  {self.iso.name}\n")
        with self.assertRaisesRegex(ValueError, "does not match"):
            module.prepare(self.iso, self.sum, self.assets, part_size=225)

    def test_bad_part_checksum_rejected(self):
        module.prepare(self.iso, self.sum, self.assets, part_size=225)
        part = next(self.assets.glob("*.iso.part*"))
        part.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            module.reassemble(self.assets)
        self.assertFalse((self.assets / self.iso.name).exists())

    def test_missing_part_rejected(self):
        module.prepare(self.iso, self.sum, self.assets, part_size=225)
        (self.assets / (self.iso.name + ".part002")).unlink()
        with self.assertRaisesRegex(ValueError, "Missing or unexpected"):
            module.reassemble(self.assets)

    def test_unsafe_checksum_filename_rejected(self):
        self.sum.write_text(f"{self.sha}  ../{self.iso.name}\n")
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            module.prepare(self.iso, self.sum, self.assets, part_size=225)

    def test_too_big_part_rejected(self):
        with self.assertRaisesRegex(ValueError, "smaller than 2 GiB"):
            module.prepare(self.iso, self.sum, self.assets, part_size=2**31)

    def test_existing_assets_refused(self):
        module.prepare(self.iso, self.sum, self.assets, part_size=225)
        with self.assertRaisesRegex(ValueError, "must be empty"):
            module.prepare(self.iso, self.sum, self.assets, part_size=225)

    def test_corrupted_reassembled_file_not_overwritten(self):
        module.prepare(self.iso, self.sum, self.assets, part_size=225)
        (self.assets / self.iso.name).write_bytes(b"wrong-existing-file")
        with self.assertRaisesRegex(ValueError, "Refusing to overwrite"):
            module.reassemble(self.assets)


if __name__ == "__main__":
    unittest.main()
