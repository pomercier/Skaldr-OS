"""Offline checks for vendor-neutral GPU and read-only recovery diagnostics."""
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1] / "archiso/airootfs"
GPU = ROOT / "usr/local/bin/skaldr-gpu-diagnostics"
RECOVERY = ROOT / "usr/local/bin/skaldr-recovery"


class GpuTests(unittest.TestCase):
    def test_parse_vulkan_summary(self):
        ns = runpy.run_path(str(GPU), run_name="safety_test")
        fn = ns["parse_vulkan"]
        self.assertFalse(fn(None)["available"])
        values = fn("deviceName = AMD Radeon RX 6800\napiVersion = 1.3.280\n")
        self.assertTrue(values["available"])
        self.assertIn("AMD Radeon RX 6800", values["devices"])
        self.assertIn("1.3.280", values["api_versions"])

    def test_diagnostic_never_changes_drivers(self):
        code = GPU.read_text()
        self.assertNotIn("pkexec chwd", code)
        self.assertNotIn("nvidia-smi -pl", code)
        self.assertNotIn("pacman -S", code)
        self.assertIn("not automatically verified", code)
        self.assertIn("ffmpeg_compiled_backends", code)


class RecoveryTests(unittest.TestCase):
    def test_snapshot_and_bootloader_status_without_modification(self):
        ns = runpy.run_path(str(RECOVERY), run_name="safety_test")
        status = ns["status"]
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "boot/grub").mkdir(parents=True)
            (root / "boot/grub/grub.cfg").write_text("# test")
            (root / "boot/vmlinuz-linux-cachyos-lts").write_text("mock")
            with patch.dict(status.__globals__, {
                "command": lambda *args: None,
                "shutil": type("Shim", (), {"which": staticmethod(lambda *args: None)}),
            }):
                data = status(root)
            self.assertEqual(data["root_filesystem"], "unknown")
            self.assertTrue(data["bootloader_config_present"]["grub"])
            self.assertFalse(data["bootloader_config_present"]["limine"])
            self.assertIn("vmlinuz-linux-cachyos-lts", data["available_kernel_filenames"])
            self.assertFalse(data["rollback_verified"])

    def test_no_destructive_recovery_automation(self):
        source = RECOVERY.read_text()
        for forbidden in ("snapper rollback", "btrfs subvolume delete",
                          "grub-install", "rm -rf"):
            self.assertNotIn(forbidden, source)


class PackagingTests(unittest.TestCase):
    def test_tools_installed_and_accessible_via_kde_center(self):
        installer = (ROOT / "usr/local/bin/skaldr-cal-inject").read_text()
        center = (ROOT / "usr/local/bin/skaldr-center").read_text()
        profile = (Path(__file__).resolve().parents[1] / "archiso/profiledef.sh").read_text()
        for name in ("skaldr-gpu-diagnostics", "skaldr-recovery"):
            with self.subTest(name=name):
                self.assertIn("/usr/local/bin/" + name, installer)
                self.assertIn(name, center)
                self.assertIn(f'["/usr/local/bin/{name}"]="0:0:755"', profile)


if __name__ == "__main__":
    unittest.main()
