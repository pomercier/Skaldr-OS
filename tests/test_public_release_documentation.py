"""Keep public release documentation consistent with pinned CI evidence.

This checks the repository's declared evidence, not current network state.
It never infers hardware certification from a published preview.
"""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/RELEASE-EVIDENCE.json"


class PublicReleaseDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = json.loads(EVIDENCE.read_text(encoding="utf-8"))
        cls.preview = cls.record["preview"]
        cls.candidate = cls.record["release_candidate"]

    def test_pinned_latest_public_release_in_all_readiness_documents(self):
        tag = self.preview["tag"]
        for filename in (
            "README.md",
            "docs/HARDWARE-TESTING.md",
            "docs/VM-ACCEPTANCE.md",
            "docs/RELEASE-READINESS.md",
            "docs/ROADMAP.md",
            "docs/VERSIONING.md",
        ):
            with self.subTest(filename=filename):
                contents = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(tag, contents)
        self.assertRegex(tag, r"^v[0-9]+\.[0-9]+\.[0-9]+-preview\.[0-9]+$")

    def test_download_and_vm_acceptance_pin_exact_source_and_checksum(self):
        sha = self.preview["source_sha"]
        iso_hash = self.preview["iso_sha256"]
        self.assertRegex(sha, r"^[0-9a-f]{40}$")
        self.assertRegex(iso_hash, r"^[0-9a-f]{64}$")
        for filename in ("README.md", "docs/VM-ACCEPTANCE.md", "docs/ROADMAP.md"):
            with self.subTest(filename=filename):
                text = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(iso_hash, text)
        for filename in ("README.md", "docs/HARDWARE-TESTING.md",
                         "docs/VM-ACCEPTANCE.md"):
            with self.subTest(filename=filename):
                text = (ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(sha, text)
        for key in ("source_tests", "iso_matrix", "public_reassembly"):
            self.assertTrue(self.preview["evidence"][key].startswith(
                "https://github.com/pomercier/Skaldr-OS/actions/runs/"
            ))

    def test_archive_table_contains_exact_latest_public_preview(self):
        row = (ROOT / "docs/VERSIONING.md").read_text(encoding="utf-8")
        tag = self.preview["tag"]
        self.assertIn(
            f"[{tag}](https://github.com/pomercier/Skaldr-OS/releases/tag/{tag})", row
        )
        self.assertIn(
            f"https://github.com/pomercier/Skaldr-OS/releases/tag/{tag}",
            (ROOT / "README.md").read_text(encoding="utf-8"),
        )

    def test_release_mode_candidate_has_separate_hash_and_vm_proof(self):
        candidate = self.candidate
        self.assertEqual(candidate["status"], "vm_validated_not_hardware_certified")
        self.assertNotEqual(candidate["iso_sha256"], self.preview["iso_sha256"])
        self.assertRegex(candidate["source_sha"], r"^[0-9a-f]{40}$")
        self.assertRegex(candidate["iso_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn(candidate["iso_sha256"],
                      (ROOT / "docs/RELEASE-READINESS.md").read_text(encoding="utf-8"))
        self.assertIn(candidate["iso_sha256"],
                      (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn(candidate["ci_evidence"],
                      (ROOT / "docs/RELEASE-READINESS.md").read_text(encoding="utf-8"))

    def test_previews_do_not_mark_real_hardware_stable(self):
        stable = self.record["stable"]
        self.assertEqual(stable["release_mode_iso"]["status"], "untested")
        self.assertEqual(stable["release_source_sha"], "")
        physical = ("nvidia_physical", "amd_physical", "intel_physical",
                    "physical_rollback", "kernel_recovery", "update_cycles")
        for key in physical:
            with self.subTest(key=key):
                self.assertEqual(stable[key]["status"], "untested")
        self.assertIn("v1.0.0", (ROOT / "docs/RELEASE-READINESS.md").read_text())


if __name__ == "__main__":
    unittest.main()
