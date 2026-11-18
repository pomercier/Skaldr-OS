"""Offline readiness reporting must never claim physical validation."""
import copy
import json
from pathlib import Path
import runpy
import unittest

ROOT = Path(__file__).resolve().parents[1]
EVALUATE = runpy.run_path(str(ROOT / "scripts/skaldr-release-readiness.py"),
                          run_name="skaldr_readiness_test")["evaluate"]
EVIDENCE = json.loads((ROOT / "docs/RELEASE-EVIDENCE.json").read_text())


class ReadinessTests(unittest.TestCase):
    def test_current_preview_is_not_stable(self):
        report = EVALUATE(EVIDENCE)
        self.assertTrue(report["recorded_preview_evidence_valid"])
        self.assertFalse(report["stable_evidence_complete"])
        self.assertFalse(report["stable_publication_automatically_authorized"])
        self.assertIn("nvidia_physical", report["stable_blockers"])
        self.assertIn("release_mode_iso", report["stable_blockers"])

    def test_missing_proof_is_not_a_pass(self):
        data = copy.deepcopy(EVIDENCE)
        data["stable"]["nvidia_physical"]["status"] = "pass"
        report = EVALUATE(data)
        self.assertIn("nvidia_physical", report["stable_blockers"])

    def test_invalid_preview_source_fails_closed(self):
        data = copy.deepcopy(EVIDENCE)
        data["preview"]["source_sha"] = "not-a-commit"
        self.assertFalse(EVALUATE(data)["recorded_preview_evidence_valid"])

    def test_documented_exception_is_limited_to_optional_features(self):
        data = copy.deepcopy(EVIDENCE)
        data["stable"]["nvidia_physical"] = {
            "status": "documented_unsupported", "evidence_url": "https://example.org/test"
        }
        data["stable"]["secure_boot"] = {
            "status": "documented_unsupported", "evidence_url": "https://example.org/test"
        }
        result = EVALUATE(data)
        self.assertIn("nvidia_physical", result["stable_blockers"])
        self.assertNotIn("secure_boot", result["stable_blockers"])

    def test_successful_evidence_still_never_auto_authorizes_release(self):
        data = copy.deepcopy(EVIDENCE)
        data["stable"]["release_source_sha"] = "f" * 40
        for key, item in data["stable"].items():
            if isinstance(item, dict):
                item.update(status="pass", evidence_url="https://example.org/review")
        result = EVALUATE(data)
        self.assertTrue(result["stable_evidence_complete"])
        self.assertFalse(result["stable_publication_automatically_authorized"])


if __name__ == "__main__":
    unittest.main()
