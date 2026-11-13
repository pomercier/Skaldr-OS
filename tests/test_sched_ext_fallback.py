"""Source-level and isolated checks for sched_ext kernel fallback.

The unit override is evaluated by systemd when the installed machine boots,
not when the Calamares installation or ISO builder executes.
"""

from pathlib import Path
import runpy
import unittest
from unittest.mock import patch


REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "archiso" / "airootfs"
DOCTOR = LIVE / "usr/local/bin/skaldr-doctor"
INJECT = LIVE / "usr/local/bin/skaldr-cal-inject"
CONDITION = LIVE / "etc/systemd/system/scx_loader.service.d/10-skaldr-kernel.conf"


class SchedExtFallbackTests(unittest.TestCase):
    def test_kernel_condition_is_shipped_to_installed_system(self):
        self.assertTrue(CONDITION.is_file())
        lines = CONDITION.read_text().splitlines()
        self.assertIn("[Unit]", lines)
        self.assertIn("ConditionPathExists=/sys/kernel/sched_ext", lines)
        self.assertNotIn("ExecStart=", CONDITION.read_text())
        # Calamares must copy the override, not just ship it in the Live ISO.
        self.assertIn("/etc/systemd/system/scx_loader.service.d/10-skaldr-kernel.conf",
                      INJECT.read_text())

    def test_doctor_reports_kernel_fallback_without_sched_ext(self):
        namespace = runpy.run_path(str(DOCTOR), run_name="skaldr_doctor_test")
        get_data = namespace["get_data"]
        for value in (None, "disabled", ""):
            with self.subTest(state=value):
                overrides = {
                    "/sys/kernel/sched_ext/state": value,
                    "/sys/kernel/sched_ext/root/ops": "scx_lavd",
                }
                def mocked_read(path, default=None):
                    return overrides.get(path, default)
                with patch.dict(get_data.__globals__, {
                    "read": mocked_read,
                    "command": lambda *args: None,
                }):
                    report = get_data()
                self.assertEqual(report["active_cpu_scheduler"],
                                 "kernel-default")
                self.assertEqual(report["cpu_scheduler_service"], "inactive")

    def test_doctor_reports_active_sched_ext_scheduler(self):
        namespace = runpy.run_path(str(DOCTOR), run_name="skaldr_doctor_test")
        get_data = namespace["get_data"]
        def mocked_read(path, default=None):
            if path == "/sys/kernel/sched_ext/state":
                return "enabled"
            if path == "/sys/kernel/sched_ext/root/ops":
                return "scx_lavd"
            return default
        with patch.dict(get_data.__globals__, {
            "read": mocked_read,
            "command": lambda *args: None,
        }):
            report = get_data()
        self.assertEqual(report["sched_ext_state"], "enabled")
        self.assertEqual(report["active_cpu_scheduler"], "scx_lavd")


if __name__ == "__main__":
    unittest.main()
