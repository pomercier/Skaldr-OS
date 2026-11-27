"""Tests for extra UEFI bootloader installation paths and fail-closed release checks."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExtraBootloaders(unittest.TestCase):
    def test_both_uefi_installations(self):
        build = (ROOT / ".github/workflows/build.yml").read_text()
        for loader in ("refind", "systemd-boot"):
            self.assertIn(
                "bootloader: " + loader + "\n            filesystem: ext4\n            firmware: uefi",
                build,
            )
        self.assertIn("test_install_calamares cachyos dailylive", build)
        self.assertIn('needs: [build, quicktest]', build)
        case = (ROOT / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertIn("Restore the exact keyboard Next action", case)
        self.assertIn('qt_send_key_combo "spc"', case)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "$text_calamares_packages"', case)
        self.assertIn("test_installed_system_cold_boot", case)

    def test_quicktest_actual_install_and_cold_boot(self):
        script = ROOT / "testcases/cachyos/dailylive/test_install_calamares"
        text = script.read_text()
        for expected in (
            '["refind"]="1"', '["systemd-boot"]="3"',
            "test_calamares_bootloader", "test_calamares_install",
            "test_calamares_finished", "test_installed_system_cold_boot",
            "test_installed_plasma_first_login", "test_installed_native_control_center",
            "Second boot still has live installer ISO attached",
        ):
            self.assertIn(expected, text)
        proc = subprocess.run(["bash", "-n", str(script)], capture_output=True,
                              text=True, timeout=10, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_preview_publishing_requires_all_eight_jobs_and_logs(self):
        gate = (ROOT / ".github/workflows/skaldr-auto-verified-preview.yml").read_text()
        for expected in (
            "Testing (refind / ext4)", "Testing (systemd-boot / ext4)",
            "Verified 8/8 real ISO",
            "grub-bios-ext4 refind-ext4 systemd-boot-ext4",
            "'refind-ext4', 'systemd-boot-ext4'",
            "Cold boot the newly installed system, without the live ISO",
            "Launch installed Skaldr Control Center in KDE Plasma",
        ):
            self.assertIn(expected, gate)

    def test_release_mode_and_dev_source_paths_match(self):
        build = (ROOT / ".github/workflows/build.yml").read_text()
        release = (ROOT / ".github/workflows/skaldr-release-candidate.yml").read_text()
        for source in (build, release):
            self.assertIn("tests/test_additional_bootloaders.py", source)
        self.assertIn("release_mode: true", release)
        self.assertNotIn("contents: write", release)


if __name__ == "__main__":
    unittest.main()
