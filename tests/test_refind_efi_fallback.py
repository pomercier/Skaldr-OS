"""Tests for the rEFInd installed EFI fallback and BIOS installer navigation."""
import runpy
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
POST = ROOT / "archiso/airootfs/usr/local/bin/skaldr-postinstall"
FIX = runpy.run_path(str(POST), run_name="skaldr_refind_test")[
    "ensure_refind_uefi_fallback"
]
PE = b"MZ" + b"\0" * 8192


class RefindEFIFallbackTests(unittest.TestCase):
    def fixture(self, tmp, *, source=True, existing=None):
        root = Path(tmp)
        elf = root / "boot/EFI/refind/refind_x64.efi"
        elf.parent.mkdir(parents=True)
        if source:
            elf.write_bytes(PE)
        if existing is not None:
            target = root / "boot/EFI/BOOT/BOOTX64.EFI"
            target.parent.mkdir(parents=True)
            target.write_bytes(existing)
        return root

    def test_creates_exact_fallback_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            self.assertTrue(FIX(root, refind_installed=True, uefi=True,
                                filesystem="vfat"))
            target = root / "boot/EFI/BOOT/BOOTX64.EFI"
            self.assertEqual(target.read_bytes(), PE)
            self.assertTrue(FIX(root, refind_installed=True, uefi=True,
                                filesystem="vfat"))

    def test_unselected_and_bios_modes_are_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            self.assertFalse(FIX(root, refind_installed=False, uefi=True,
                                 filesystem="vfat"))
            self.assertFalse(FIX(root, refind_installed=True, uefi=False,
                                 filesystem="vfat"))
            self.assertFalse((root / "boot/EFI/BOOT/BOOTX64.EFI").exists())

    def test_fails_on_wrong_mount_or_bad_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            with self.assertRaisesRegex(RuntimeError, "mounted FAT ESP"):
                FIX(root, refind_installed=True, uefi=True, filesystem="ext4")
            with self.assertRaisesRegex(RuntimeError, "mounted FAT ESP"):
                FIX(root, refind_installed=True, uefi=True, filesystem=None)
            (root / "boot/EFI/refind/refind_x64.efi").write_bytes(b"BAD")
            with self.assertRaisesRegex(RuntimeError, "not a PE"):
                FIX(root, refind_installed=True, uefi=True, filesystem="vfat")
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp, source=False)
            with self.assertRaisesRegex(RuntimeError, "EFI binary missing"):
                FIX(root, refind_installed=True, uefi=True, filesystem="vfat")

    def test_refuses_overwrite_and_unsafe_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp, existing=b"MZ" + b"different" * 1200)
            with self.assertRaisesRegex(RuntimeError, "already owns"):
                FIX(root, refind_installed=True, uefi=True, filesystem="vfat")
        with tempfile.TemporaryDirectory() as tmp:
            root = self.fixture(tmp)
            link = root / "boot/EFI/BOOT"
            link.symlink_to(root / "boot/EFI/refind", target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError, "symlinked"):
                FIX(root, refind_installed=True, uefi=True, filesystem="vfat")

    def test_chroot_esp_detection_requires_separate_device_and_target_lookup(self):
        post = POST.read_text(encoding="utf-8")
        # Limine legitimately has its own independent mount test. Inspect
        # the rEFInd function only, not every other bootloader's code.
        code = post.split("def ensure_refind_uefi_fallback(", 1)[1].split(
            "def main():", 1
        )[0]
        self.assertIn('["findmnt", "-rnT", str(esp), "-o", "FSTYPE"]', code)
        self.assertNotIn('["findmnt", "-rnM", str(esp), "-o", "FSTYPE"]', code)
        self.assertIn("os.stat(esp).st_dev == os.stat(root).st_dev", code)
        self.assertIn("not an exact mounted FAT ESP", code)

    def test_real_install_and_release_gates_stay_enabled(self):
        self.assertIn("ensure_refind_uefi_fallback()",
                      POST.read_text(encoding="utf-8"))
        case = (ROOT / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertIn("BIOS partition Next QMP click failed", case)
        self.assertIn("test_installed_system_cold_boot", case)
        self.assertIn("test_installed_native_control_center", case)
        for workflow in (".github/workflows/build.yml",
                         ".github/workflows/skaldr-release-candidate.yml"):
            self.assertIn("tests/test_refind_efi_fallback.py",
                          (ROOT / workflow).read_text())


if __name__ == "__main__":
    unittest.main()
