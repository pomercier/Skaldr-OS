"""Scan root subvolume flags in installed boot files without modifying them."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import runpy

SCRIPT = Path(__file__).resolve().parents[1] / (
    "archiso/airootfs/usr/local/bin/skaldr-recovery"
)
namespace = runpy.run_path(str(SCRIPT))
configured = namespace["configured_boot_root_overrides"]
fstab_override = namespace["fstab_root_subvolume_override"]
status = namespace["status"]


class BootConfigurationRecoveryTests(TestCase):
    def test_detect_grub_limine_and_systemd_boot_entries(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "boot/grub").mkdir(parents=True)
            (root / "boot/grub/grub.cfg").write_text(
                "# rootflags=subvol=ignore\n"
                "linux /vmlinuz root=UUID=1234 rootflags=subvol=@,compress=zstd\n"
            )
            (root / "boot").mkdir(exist_ok=True)
            (root / "boot/limine.conf").write_text(
                "cmdline: quiet rootflags=subvolid=258\n"
            )
            entries = root / "boot/loader/entries"
            entries.mkdir(parents=True)
            (entries / "skaldr.conf").write_text(
                "options root=/dev/vda rootflags=\"subvol=@safe\" quiet\n"
            )
            (root / "etc/default").mkdir(parents=True)
            (root / "etc/default/grub").write_text(
                'GRUB_CMDLINE_LINUX_DEFAULT="quiet rootflags=subvol=@next,compress=zstd"\n'
            )
            (root / "etc/default/limine").write_text(
                'KERNEL_CMDLINE[default]="quiet rootflags=subvolid=311"\n'
            )
            (root / "etc/kernel").mkdir(parents=True)
            (root / "etc/kernel/cmdline").write_text(
                "quiet rootflags=subvol=@future\n"
            )
            values, checked = configured(root)
        self.assertEqual(values["grub"], ["subvol=@", "subvol=@next"])
        self.assertEqual(values["limine"], ["subvolid=258", "subvolid=311"])
        self.assertEqual(values["systemd_boot"], ["subvol=@safe"])
        self.assertEqual(values["kernel_cmdline"], ["subvol=@future"])
        self.assertEqual(checked, {
            "grub": True, "limine": True, "systemd_boot": True,
            "kernel_cmdline": True,
        })

    def test_fstab_root_subvolume_and_other_mounts(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "etc").mkdir()
            (root / "etc/fstab").write_text(
                "# UUID=old / btrfs subvol=ignore 0 0\n"
                "UUID=home /home btrfs subvol=@home 0 0\n"
                "UUID=root / btrfs rw,compress=zstd,subvol=@ 0 0\n"
            )
            self.assertEqual(fstab_override(root), "subvol=@")

    def test_scan_does_not_claim_success_or_change_files(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "etc").mkdir()
            fstab = root / "etc/fstab"
            fstab.write_text("UUID=root / btrfs rw,subvol=@ 0 0\n")
            original = fstab.read_bytes()
            with patch.dict(status.__globals__, {"command": lambda *a: None}):
                report = status(root)
            self.assertEqual(fstab.read_bytes(), original)
        self.assertEqual(report["fstab_root_subvolume_override"], "subvol=@")
        self.assertTrue(report["boot_subvolume_override_detected"])
        self.assertIs(report["default_subvolume_change_sufficient_for_boot"], False)
        self.assertFalse(report["rollback_verified"])

    def test_no_entries_is_unknown_not_rollback_certified(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            with patch.dict(status.__globals__, {"command": lambda *a: None}):
                report = status(root)
        self.assertEqual(report["boot_config_sources_checked"],
                         {"grub": False, "limine": False,
                          "systemd_boot": False, "kernel_cmdline": False})
        self.assertIsNone(report["default_subvolume_change_sufficient_for_boot"])
        self.assertFalse(report["rollback_verified"])
