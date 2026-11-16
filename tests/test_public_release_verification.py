"""Independent public-release verification must fail closed, not trust release manifests."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-verify-public-release.py"
LOCK = ROOT / "docs/PUBLIC-PREVIEW-1-LOCK.json"
WORKFLOW = ROOT / ".github/workflows/skaldr-public-release-verification.yml"
CODE = runpy.run_path(str(SCRIPT), run_name="unit_test")
validate_lock = CODE["validate_lock"]
validate_release_metadata = CODE["validate_release_metadata"]
validate_downloaded_assets = CODE["validate_downloaded_assets"]
verify_reassembly = CODE["verify_reassembly"]
VerificationError = CODE["ReleaseVerificationError"]


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


class PublicReleaseVerificationTests(unittest.TestCase):
    def setUp(self):
        self.lock = validate_lock(json.loads(LOCK.read_text()))
        self.assets = CODE["expected_assets"](self.lock)
        self.meta = {
            "tag_name": self.lock["tag"],
            "target_commitish": self.lock["source_sha"],
            "prerelease": True, "draft": False, "published_at": "2026-11-13T22:23:49Z",
            "assets": [
                {"name": name, "size": length, "state": "uploaded",
                 "browser_download_url": (
                     "https://github.com/pomercier/Skaldr-OS/releases/download/"
                     + self.lock["tag"] + "/" + name)}
                for name, length in self.assets.items()
            ],
        }

    def test_pinned_lock_is_from_validated_five_job_iso(self):
        self.assertEqual(self.lock["source_sha"],
                         "b391fc35f4eaade3c1ff5231c33c10f63770bda6")
        self.assertEqual(self.lock["validated_iso_run_id"], 43507233020)
        self.assertEqual(self.lock["iso_sha256"],
                         "b553c0e4cfe01e1de0c857f1dc4c70ac89d41a762bdb01750c770bb77069ec49")
        self.assertEqual(len(self.assets), 7)
        self.assertEqual(len(self.lock["parts"]), 3)
        self.assertTrue(validate_release_metadata(self.meta, self.lock))

    def test_metadata_requires_exact_tag_source_and_prerelease(self):
        for k, bad in [("tag_name", "v0.1.0-preview.2"),
                       ("target_commitish", "a" * 40),
                       ("prerelease", False), ("draft", True),
                       ("published_at", "")]:
            with self.subTest(k=k):
                m = deepcopy(self.meta)
                m[k] = bad
                with self.assertRaises(VerificationError):
                    validate_release_metadata(m, self.lock)

    def test_asset_count_duplicate_size_and_url_are_mandatory(self):
        for mutate in (
            lambda m: m["assets"].pop(),
            lambda m: m["assets"][0].update(size=999),
            lambda m: m["assets"][0].update(
                browser_download_url="https://example.com/fake-ISO"),
            lambda m: m["assets"][0].update(name=m["assets"][1]["name"]),
        ):
            m = deepcopy(self.meta)
            mutate(m)
            with self.assertRaises(VerificationError):
                validate_release_metadata(m, self.lock)

    def make_synthetic_assets(self, folder):
        pieces = [b"the first piece", b"the second piece"]
        name = "skaldr-0.1.0-dev.1-x86_64.iso"
        parts = [
            {"name": f"{name}.part{i+1:03d}",
             "sha256": digest(blob), "bytes": len(blob)}
            for i, blob in enumerate(pieces)
        ]
        for item, content in zip(parts, pieces):
            (folder / item["name"]).write_bytes(content)
        manifest = digest(b"".join(pieces)) + "  " + name + "\n"
        parts_manifest = "".join(x["sha256"] + "  " + x["name"] + "\n"
                                 for x in parts)
        small = {
            "SHA256SUMS": manifest.encode(),
            "SHA256SUMS.parts": parts_manifest.encode(),
            "ASSEMBLE.txt": b"How to reconstruct\n",
            # This untrusted file is never executed by our verification tool.
            "reassemble-skaldr-iso.py": b'raise RuntimeError("UNTRUSTED")\n',
        }
        for key, content in small.items():
            (folder / key).write_bytes(content)
        synthetic = {
            "tag": "v0.1.0-preview.9", "source_sha": "f" * 40,
            "iso_name": name, "iso_sha256": digest(b"".join(pieces)),
            "parts": parts,
            "small_assets": {k: {"bytes": len(v), "sha256": digest(v)}
                             for k, v in small.items()},
        }
        return synthetic

    def test_synthetic_complete_release_can_reassemble_without_remote_code(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            lock = self.make_synthetic_assets(folder)
            self.assertTrue(validate_downloaded_assets(folder, lock))
            report = verify_reassembly(folder, lock)
            self.assertEqual(report["status"], "PASS")
            self.assertEqual((folder / lock["iso_name"]).read_bytes(),
                             b"the first piecethe second piece")

    def test_tampered_asset_with_same_size_fails_sha256(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            lock = self.make_synthetic_assets(folder)
            part = folder / lock["parts"][0]["name"]
            part.write_bytes(b"X" * part.stat().st_size)
            self.assertTrue(validate_downloaded_assets(folder, lock))
            with self.assertRaisesRegex(VerificationError, "did not reassemble"):
                verify_reassembly(folder, lock)

    def test_tampered_small_helper_or_missing_asset_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            lock = self.make_synthetic_assets(folder)
            (folder / "ASSEMBLE.txt").write_bytes(b"x" * lock["small_assets"]["ASSEMBLE.txt"]["bytes"])
            with self.assertRaisesRegex(VerificationError, "differs"):
                validate_downloaded_assets(folder, lock)
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            lock = self.make_synthetic_assets(folder)
            (folder / lock["parts"][1]["name"]).unlink()
            with self.assertRaises(VerificationError):
                validate_downloaded_assets(folder, lock)

    def test_workflow_does_not_publish_or_execute_downloaded_helper(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("gh release download v0.1.0-preview.1", workflow)
        self.assertIn("scripts/skaldr-verify-public-release.py verify", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)
        for prohibited in ("gh release create", "git push", "contents: write"):
            self.assertNotIn(prohibited, workflow)
        script = SCRIPT.read_text()
        self.assertIn('"reassemble", "--directory", str(directory)', script)
        self.assertNotIn('str(directory / "reassemble-skaldr-iso.py")', script)


if __name__ == "__main__":
    unittest.main()
