"""The physical evidence report is never automatic hardware certification."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "archiso/airootfs/usr/local/bin/skaldr-physical-evidence"
MODULE = runpy.run_path(str(SCRIPT), run_name="skaldr_physical_test")
CREATE = MODULE["create_report"]
WRITE = MODULE["write_private"]


class PhysicalEvidenceTests(unittest.TestCase):
    def test_nothing_is_automatically_marked_pass(self):
        report = CREATE(probe={"gpu_vendor_families": ["NVIDIA"]})
        self.assertTrue(all(v == "untested" for v in report["manual_checks"].values()))
        self.assertFalse(report["stable_release_certified"])
        self.assertEqual(report["physical_machine"], "unverified")
        self.assertEqual(report["status"], "self_reported_pending_independent_review")

    def test_pass_requires_physical_confirmation(self):
        with self.assertRaisesRegex(ValueError, "physical-machine attestation"):
            CREATE({"cold_boot": "pass"})
        report = CREATE({"cold_boot": "pass", "snapshot_rollback": "fail"},
                        physical_attested=True)
        self.assertEqual(report["manual_checks"]["cold_boot"], "pass")
        self.assertEqual(report["manual_checks"]["snapshot_rollback"], "fail")
        self.assertFalse(report["stable_release_certified"])

    def test_invalid_results_or_hash_are_rejected(self):
        for case in ({"not_a_check": "pass"}, {"cold_boot": "maybe"}):
            with self.assertRaises(ValueError):
                CREATE(case, physical_attested=True)
        with self.assertRaisesRegex(ValueError, "ISO SHA-256"):
            CREATE(iso_sha256="bad")
        with self.assertRaises(ValueError):
            CREATE(mode="virtual")

    def test_allowlist_filters_sensitive_probe_fields(self):
        probe = {
            "schema": "skaldr.hardware-observations.v1",
            "architecture": "x86_64",
            "gpu_vendor_families": ["NVIDIA", "NVIDIA", "private-computer"],
            "kernel": "7.3.1-1-cachyos",
            "hostname": "private-computer",
            "email": "private@example.com",
            "build_identity": {
                "git_revision": "a" * 40,
                "version": "0.1.0-dev.226",
                "account_name": "private-computer",
            },
        }
        report = CREATE(probe=probe)
        self.assertEqual(report["observations"]["gpu_vendor_families"], ["NVIDIA"])
        self.assertEqual(report["observations"]["build_identity"]["git_revision"], "a" * 40)
        encoded = json.dumps(report)
        for forbidden in ("private-computer", "private@example.com", "account_name"):
            self.assertNotIn(forbidden, encoded)

    def test_private_report_is_exclusive_and_symlinks_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "physical.json"
            WRITE(path, "{}\n")
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                WRITE(path, "overwrite")
            other = Path(tmp) / "linked.json"
            other.symlink_to(path)
            with self.assertRaisesRegex(ValueError, "symlink"):
                WRITE(other, "overwrite")
            self.assertEqual(path.read_text(), "{}\n")

    def test_installed_payload_and_syntax_registered(self):
        inject = (ROOT / "archiso/airootfs/usr/local/bin/skaldr-cal-inject").read_text()
        profile = (ROOT / "archiso/profiledef.sh").read_text()
        workflow = (ROOT / ".github/workflows/skaldr-checks.yml").read_text()
        self.assertIn('"/usr/local/bin/skaldr-physical-evidence"', inject)
        self.assertIn('["/usr/local/bin/skaldr-physical-evidence"]="0:0:755"', profile)
        self.assertIn("skaldr-physical-evidence", workflow)


if __name__ == "__main__":
    unittest.main()
