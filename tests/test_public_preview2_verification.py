"""Release-event gate for preview.2, cryptographically pinned to a validated ISO."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-verify-public-release.py"
LOCK = ROOT / "docs/PUBLIC-PREVIEW-2-LOCK.json"
WORKFLOW = ROOT / ".github/workflows/skaldr-preview2-public-verification.yml"
CODE = runpy.run_path(str(SCRIPT), run_name="preview2_unit_test")
Error = CODE["ReleaseVerificationError"]
verify_lock = CODE["validate_lock"]
verify_metadata = CODE["validate_release_metadata"]
verify_files = CODE["validate_downloaded_assets"]
reassemble = CODE["verify_reassembly"]


class PreviewTwoReleaseIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.lock = verify_lock(json.loads(LOCK.read_text()))
        self.expected = CODE["expected_assets"](self.lock)

    def test_candidate_is_exact_successful_five_job_iso(self):
        self.assertEqual(self.lock["tag"], "v0.1.0-preview.2")
        self.assertEqual(self.lock["source_sha"],
                         "4bf13febf464e95f452406ed98cd3fc30cd3c77c")
        self.assertEqual(self.lock["validated_iso_run_id"], 43801626684)
        self.assertEqual(self.lock["source_checks_run_id"], 43801626727)
        self.assertEqual(self.lock["source_checks_run_id"], 43801626727)
        self.assertEqual(self.lock["iso_name"], "skaldr-0.1.0-dev.123-x86_64.iso")
        self.assertEqual(self.lock["iso_sha256"],
                         "07be14cdf59a37cafd1068801fd99ab9cd1b9c7af98a4acd12ce1975d57ab47a")
        self.assertEqual(len(self.lock["parts"]), 3)
        self.assertEqual(len(self.expected), 7)
        self.assertEqual(self.lock["small_assets"]["ASSEMBLE.txt"]["bytes"], 529)

    def test_unpinned_final_part_size_does_not_waive_sha256(self):
        last = self.lock["parts"][-1]
        self.assertNotIn("bytes", last)  # Original CI manifest pins the SHA256 instead.
        self.assertEqual(self.expected[last["name"]], None)
        self.assertRegex(last["sha256"], r"^[0-9a-f]{64}$")
        for illegal in (0, -5, False, 2 * 1024**3, "200MiB"):
            test = deepcopy(self.lock)
            test["parts"][-1]["bytes"] = illegal
            with self.subTest(illegal=illegal):
                with self.assertRaises(Error):
                    verify_lock(test)

    def test_metadata_rejects_unauthorized_tag_and_mismatched_origin(self):
        item_sizes = {name: size if size is not None else 210000000
                      for name, size in self.expected.items()}
        metadata = {
            "tag_name": "v0.1.0-preview.2",
            "target_commitish": self.lock["source_sha"],
            "draft": False,
            "prerelease": True,
            "published_at": "2026-11-16T00:00:00Z",
            "assets": [
                {"name": name, "size": size, "state": "uploaded",
                 "browser_download_url":
                 f"https://github.com/pomercier/Skaldr-OS/releases/download/v0.1.0-preview.2/{name}"}
                for name, size in item_sizes.items()
            ],
        }
        self.assertTrue(verify_metadata(metadata, self.lock))
        for key, illegal in [("tag_name", "v0.1.0-preview.1"),
                             ("target_commitish", "f" * 40),
                             ("prerelease", False)]:
            wrong = deepcopy(metadata)
            wrong[key] = illegal
            with self.subTest(key=key), self.assertRaises(Error):
                verify_metadata(wrong, self.lock)
        for size in (-1, 0, 2 * 1024**3):
            wrong = deepcopy(metadata)
            unknown_part = self.lock["parts"][-1]["name"]
            next(x for x in wrong["assets"] if x["name"] == unknown_part)["size"] = size
            with self.subTest(size=size), self.assertRaises(Error):
                verify_metadata(wrong, self.lock)

    def test_reassembly_verifies_hashes_even_when_last_size_is_unpinned(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            folder = root / "release-assets"
            folder.mkdir()
            iso_name = "skaldr-0.1.0-dev.1-x86_64.iso"
            chunks = (b"original-version", b"restored-version")
            sha = lambda b: hashlib.sha256(b).hexdigest()
            parts = []
            for number, chunk in enumerate(chunks, 1):
                name = f"{iso_name}.part{number:03d}"
                (folder / name).write_bytes(chunk)
                info = {"name": name, "sha256": sha(chunk)}
                if number == 1:
                    info["bytes"] = len(chunk)
                parts.append(info)
            helpers = {
                "SHA256SUMS": f'{sha(b"".join(chunks))}  {iso_name}\n'.encode(),
                "SHA256SUMS.parts": "".join(f'{x["sha256"]}  {x["name"]}\n' for x in parts).encode(),
                "ASSEMBLE.txt": b"Test instructions\n",
                "reassemble-skaldr-iso.py": b"DO NOT EXECUTE THIS DOWNLOAD\n",
            }
            for name, blob in helpers.items():
                (folder / name).write_bytes(blob)
            lock = {
                "tag": "v0.1.0-preview.2", "source_sha": "a" * 40,
                "iso_name": iso_name, "iso_sha256": sha(b"".join(chunks)),
                "parts": parts,
                "small_assets": {name: {"bytes": len(data), "sha256": sha(data)}
                                 for name, data in helpers.items()},
            }
            self.assertTrue(verify_files(folder, lock))
            lock_path = root / "candidate-lock.json"
            lock_path.write_text(json.dumps(lock), encoding="utf-8")
            self.assertEqual(CODE["main"](["assets", "--lock", str(lock_path),
                                           "--directory", str(folder)]), 0)
            result = reassemble(folder, lock)
            self.assertEqual(result["bytes"], sum(map(len, chunks)))
            self.assertEqual(result["status"], "PASS")
            self.assertEqual((folder / iso_name).read_bytes(), b"".join(chunks))
            (folder / iso_name).unlink()
            (folder / parts[-1]["name"]).write_bytes(b"TAMPERED-VERSION!"[:len(chunks[-1])])
            with self.assertRaisesRegex(Error, "did not reassemble"):
                reassemble(folder, lock)

    def test_manual_release_is_pinned_and_automatically_checks_public_assets(self):
        workflow = (ROOT / ".github/workflows/skaldr-release.yml").read_text()
        self.assertIn('if [[ "$RELEASE_VERSION" == "v0.1.0-preview.2" ]]; then', workflow)
        self.assertIn('docs/PUBLIC-PREVIEW-2-LOCK.json', workflow)
        self.assertIn('scripts/skaldr-verify-public-release.py assets', workflow)
        self.assertIn('sha256sum --check SHA256SUMS.parts', workflow)
        self.assertIn('Preserve trusted preview.2 lock and prepublication verifier', workflow)
        self.assertIn('skaldr-release-gate/skaldr-verify-public-release.py', workflow)
        self.assertIn('skaldr-release-gate/PUBLIC-PREVIEW-2-LOCK.json', workflow)
        self.assertIn('[[ "$candidate" != "$pinned_sha" ]]', workflow)
        self.assertIn('independent_preview2_integrity:', workflow)
        self.assertIn('needs: release', workflow)
        self.assertIn("inputs.version == 'v0.1.0-preview.2'", workflow)
        self.assertIn('gh release download v0.1.0-preview.2', workflow)
        self.assertIn('scripts/skaldr-verify-public-release.py verify', workflow)
        self.assertIn('ref: master', workflow)
        self.assertIn('contents: read', workflow)
        self.assertIn('name: skaldr-published-preview2-integrity', workflow)

    def test_release_event_verifies_exact_tag_without_publishing(self):
        script = WORKFLOW.read_text()
        self.assertIn("types: [published]", script)
        self.assertIn("github.event.release.tag_name == 'v0.1.0-preview.2'", script)
        self.assertIn("docs/PUBLIC-PREVIEW-2-LOCK.json", script)
        self.assertIn("gh release download", script)
        self.assertIn("scripts/skaldr-verify-public-release.py verify", script)
        self.assertIn("permissions:\n  contents: read", script)
        self.assertIn("actions/checkout@v4", script)
        for forbidden in ("gh release create", "gh release upload", "git push",
                          "contents: write", "gh workflow run"):
            self.assertNotIn(forbidden, script)


if __name__ == "__main__":
    unittest.main()
