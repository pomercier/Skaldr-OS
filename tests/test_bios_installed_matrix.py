"""Real BIOS-installed GRUB/ext4 CI must not be confused with BIOS live boot."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BiosInstalledMatrixTests(unittest.TestCase):
    def test_full_matrix_includes_separate_legacy_install(self):
        build = (ROOT / ".github/workflows/build.yml").read_text()
        self.assertIn("bootloader: grub-bios\n            filesystem: ext4\n            firmware: bios", build)
        self.assertIn("bootloader: bios\n            filesystem: live\n            firmware: bios", build)
        self.assertIn("bootloader: grub\n            filesystem: ext4\n            firmware: uefi", build)
        self.assertIn("bootloader: limine\n            filesystem: btrfs\n            firmware: uefi", build)
        self.assertIn('TEST_FIRMWARE: "${{ matrix.firmware }}"', build)
        self.assertIn("matrix.bootloader == 'grub-bios' && 'grub' || matrix.bootloader", build)
        self.assertIn("if [ \"${{ matrix.firmware }}\" = \"bios\" ]; then", build)
        self.assertIn("./quicktest/quicktest test_install_calamares cachyos dailylive", build)

    def test_real_install_checks_disk_boot_and_requires_password(self):
        code = (ROOT / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertIn("function test_post_boot_bios()", code)
        self.assertIn("Requested legacy BIOS install launched with UEFI firmware", code)
        self.assertIn("Legacy installed system unexpectedly rebooted under UEFI", code)
        self.assertIn("Second boot still has live installer ISO attached", code)
        self.assertIn('qt_send_string_return "$test_password"', code)
        self.assertIn('test_installed_plasma_first_login', code)
        self.assertIn('test_installed_native_control_center', code)


if __name__ == "__main__":
    unittest.main()
