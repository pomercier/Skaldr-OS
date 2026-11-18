"""Physical-hardware observer must remain read-only and identifier-free."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = runpy.run_path(str(ROOT / "archiso/airootfs/usr/local/bin/skaldr-hardware-probe"),
                        run_name="hardware_probe_tests")
COLLECT = MODULE["collect"]
WRITE = MODULE["write_private"]


class HardwareProbeTests(unittest.TestCase):
    def test_gpu_vendor_and_identity_are_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            pci = base / "sys/bus/pci/devices/0000:01:00.0"
            pci.mkdir(parents=True)
            (pci / "class").write_text("0x030000")
            (pci / "vendor").write_text("0x10de")
            identity = base / "usr/share/skaldr"
            identity.mkdir(parents=True)
            (identity / "build.json").write_text(json.dumps({
                "version": "0.1.0-dev.149+g1234abcd",
                "git_revision": "a" * 40,
                "hostname": "private-machine", "user": "private-user",
                "serial": "private-serial",
            }))
            proc = base / "proc"
            proc.mkdir()
            (proc / "meminfo").write_text("MemTotal:       33554432 kB\n")
            report = COLLECT(base, {"XDG_SESSION_TYPE": "wayland",
                                    "XDG_CURRENT_DESKTOP": "KDE:Plasma",
                                    "HOME": "/home/private-user"})
            self.assertEqual(report["gpu_vendor_families"], ["NVIDIA"])
            self.assertEqual(report["ram_total_gib_approx"], 32.0)
            self.assertEqual(report["session_type"], "wayland")
            self.assertTrue(report["plasma_session"])
            content = json.dumps(report)
            for forbidden in ("private-machine", "private-user", "private-serial",
                              "0000:01:00.0", "/home/"):
                self.assertNotIn(forbidden, content)
            self.assertEqual(report["status"], "observations_only_not_certified")

    def test_calamares_copies_probe_to_installed_system(self):
        inject = runpy.run_path(
            str(ROOT / "archiso/airootfs/usr/local/bin/skaldr-cal-inject"),
            run_name="calamares_inject_test")
        self.assertIn("/usr/local/bin/skaldr-hardware-probe", inject["FILES"])

    def test_no_existing_report_overwrite_and_private_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report.json"
            WRITE(target, "{}\n")
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                WRITE(target, "overwrite")
            self.assertEqual(target.read_text(), "{}\n")

    def test_invalid_identity_and_unknown_gpu_do_not_fake_certification(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            report = COLLECT(base, {"XDG_SESSION_TYPE": "custom-desktop"})
            self.assertEqual(report["build_identity"], {})
            self.assertEqual(report["gpu_vendor_families"], [])
            self.assertEqual(report["session_type"], "unknown")
            self.assertIn("cold_boot", report["manual_verification_required"])


if __name__ == "__main__":
    unittest.main()
