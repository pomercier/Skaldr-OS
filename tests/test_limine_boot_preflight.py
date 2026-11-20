"""Regression coverage for read-only UEFI Limine installation preflight."""
from pathlib import Path
import runpy
import tempfile
import unittest

POSTINSTALL = Path(__file__).resolve().parents[1] / "archiso/airootfs/usr/local/bin/skaldr-postinstall"


class LiminePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.check = staticmethod(runpy.run_path(str(POSTINSTALL), run_name="test")
                                 ["verify_limine_uefi_esp"])

    def fixture(self, root, *, prefs='ESP_PATH="/boot"\n',
                content='timeout: 5\n/+Skaldr OS\n//Linux\n protocol: linux\n',
                efi='EFI/limine/limine_x64.efi'):
        cfg = root / "etc/default/limine"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(prefs)
        esp = root / "boot"
        esp.mkdir()
        if content is not None:
            (esp / "limine.conf").write_text(content)
        if efi is not None:
            binary = esp / efi
            binary.parent.mkdir(parents=True, exist_ok=True)
            binary.write_bytes(b'MZ')

    def test_valid_fat_esp_config_and_uefi_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            self.assertTrue(self.check(root, limine_installed=True, uefi=True,
                                       filesystem="vfat"))

    def test_unselected_limine_does_not_affect_grub(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(self.check(Path(tmp), limine_installed=False,
                                        uefi=True, filesystem="ext4"))

    def test_legacy_bios_not_regressed(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(self.check(Path(tmp), limine_installed=True,
                                        uefi=False, filesystem="ext4"))

    def test_missing_config_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, content=None)
            with self.assertRaisesRegex(RuntimeError, "limine.conf missing"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_config_without_bootable_linux_entry_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, content="timeout: 5\n/+Skaldr OS\n")
            with self.assertRaisesRegex(RuntimeError, "no Linux boot entry"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_config_on_unmounted_boot_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            with self.assertRaisesRegex(RuntimeError, "not an exact mounted FAT"):
                self.check(root, limine_installed=True, uefi=True, filesystem=None)

    def test_config_on_ext4_instead_of_fat_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            with self.assertRaisesRegex(RuntimeError, "not an exact mounted FAT"):
                self.check(root, limine_installed=True, uefi=True, filesystem="ext4")

    def test_missing_efi_loader_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, efi=None)
            with self.assertRaisesRegex(RuntimeError, "EFI executable missing"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_valid_uefi_fallback_loader_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, efi="EFI/BOOT/BOOTX64.EFI")
            self.assertTrue(self.check(root, limine_installed=True, uefi=True,
                                       filesystem="vfat"))

    def test_missing_esp_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, prefs="BOOT_ORDER=linux\n")
            with self.assertRaisesRegex(RuntimeError, "exactly one ESP_PATH"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_duplicate_esp_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, prefs='ESP_PATH="/boot"\nESP_PATH="/boot/efi"\n')
            with self.assertRaisesRegex(RuntimeError, "exactly one ESP_PATH"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_path_traversal_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, prefs='ESP_PATH="/boot/../etc"\n')
            with self.assertRaisesRegex(RuntimeError, "unsafe ESP_PATH"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_missing_esp_directory_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root, prefs='ESP_PATH="/efi"\n')
            with self.assertRaisesRegex(RuntimeError, "ESP path is missing"):
                self.check(root, limine_installed=True, uefi=True, filesystem="vfat")

    def test_correct_config_but_efi_not_on_fat_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.fixture(root)
            with self.assertRaisesRegex(RuntimeError, "not an exact mounted FAT"):
                self.check(root, limine_installed=True, uefi=True, filesystem="btrfs")


if __name__ == "__main__":
    unittest.main()
