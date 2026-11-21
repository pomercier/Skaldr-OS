"""Fail-closed virtual graphics installer integration regression tests."""
import runpy
from pathlib import Path
import tempfile
import unittest

import yaml
import test_edition_branding as branding

ROOT = Path(__file__).resolve().parents[1]
TOOLS = runpy.run_path(
    str(ROOT / "archiso/airootfs/usr/local/bin/skaldr-cal-config"),
    run_name="virtual_gpu_tests")


def pci_display(root, n, vendor, klass="0x030000"):
    device = root / "sys/bus/pci/devices" / ("0000:00:%02x.0" % n)
    device.mkdir(parents=True)
    (device / "class").write_text(klass)
    (device / "vendor").write_text(vendor)


class VirtualChwdTests(unittest.TestCase):
    def test_known_virtual_displays_and_passthrough(self):
        for vendor, profile in (("0x1af4", "qemu"),
                                ("0x1b36", "qemu"),
                                ("0x1234", "qemu"),
                                ("0x15ad", "vmware"),
                                ("0x80ee", "virtualbox"),
                                ("0x1414", "hyperv")):
            with self.subTest(vendor=vendor), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                pci_display(root, 1, vendor)
                self.assertEqual(TOOLS["virtual_display_profile"](root), profile)
                pci_display(root, 2, "0x10de")
                self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_virtualbox_vmsvga_uses_virtualbox_guest_utils(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci_display(root, 1, "0x15ad")
            dmi = root / "sys/class/dmi/id"
            dmi.mkdir(parents=True)
            (dmi / "product_name").write_text("VirtualBox")
            (dmi / "sys_vendor").write_text("innotek GmbH")
            profile = TOOLS["virtual_display_profile"](root)
            self.assertEqual(profile, "virtualbox")
            self.assertIn("virtualbox-guest-utils", TOOLS["VIRTUAL_KDE_PACKAGES"][profile])
            self.assertNotIn("open-vm-tools", TOOLS["VIRTUAL_KDE_PACKAGES"][profile])
            pci_display(root, 2, "0x10de")
            self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_vmware_dmi_does_not_change_existing_behavior(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci_display(root, 1, "0x15ad")
            dmi = root / "sys/class/dmi/id"
            dmi.mkdir(parents=True)
            (dmi / "product_name").write_text("VMware Virtual Platform")
            self.assertEqual(TOOLS["virtual_display_profile"](root), "vmware")

    def test_contradictory_dmi_preserves_chwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci_display(root, 1, "0x15ad")
            dmi = root / "sys/class/dmi/id"
            dmi.mkdir(parents=True)
            (dmi / "product_name").write_text("VirtualBox")
            (dmi / "sys_vendor").write_text("VMware, Inc.")
            self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_vmsvga_installer_integration_preserves_user_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branding.CalamaresBrandingChecks().make_fixture(root)
            pci_display(root, 1, "0x15ad")
            dmi = root / "sys/class/dmi/id"
            dmi.mkdir(parents=True)
            (dmi / "product_name").write_text("VirtualBox")
            (dmi / "sys_vendor").write_text("innotek GmbH")
            original = root / "usr/share/calamares/settings_online.conf"
            original.write_text(original.read_text().replace(
                "branding: cachyos",
                "- exec:\n  - partition\n  - chwd\n  - users\nbranding: cachyos"))
            TOOLS["prepare"](root)
            settings = yaml.safe_load((root / "etc/calamares/settings.conf").read_text())
            self.assertNotIn("chwd", settings["sequence"][1]["exec"])
            self.assertIn("users", settings["sequence"][1]["exec"])
            groups = yaml.safe_load((root / "etc/calamares/modules/netinstall.yaml").read_text())
            kde = next(item for item in groups if item["name"] == "KDE-Desktop")
            self.assertIn("virtualbox-guest-utils", kde["packages"])
            self.assertNotIn("open-vm-tools", kde["packages"])
            self.assertIn("mesa", kde["packages"])

    def test_cirrus_physical_without_subsystem_preserves_chwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci_display(root, 1, "0x1013")
            self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_cirrus_qemu_subsystem_is_accepted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci_display(root, 1, "0x1013")
            pci = root / "sys/bus/pci/devices/0000:00:01.0"
            (pci / "device").write_text("0x00b8")
            (pci / "subsystem_vendor").write_text("0x1af4")
            (pci / "subsystem_device").write_text("0x1100")
            self.assertEqual(TOOLS["virtual_display_profile"](root), "qemu")

    def test_cirrus_wrong_subsystem_or_device_preserves_chwd(self):
        for field, replacement in (("device", "0x004c"),
                                   ("subsystem_vendor", "0x0000"),
                                   ("subsystem_device", "0x0001")):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                pci_display(root, 1, "0x1013")
                pci = root / "sys/bus/pci/devices/0000:00:01.0"
                for name, value in (("device", "0x00b8"),
                                    ("subsystem_vendor", "0x1af4"),
                                    ("subsystem_device", "0x1100")):
                    (pci / name).write_text(replacement if name == field else value)
                self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_cirrus_mixed_physical_gpu_preserves_chwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pci_display(root, 1, "0x1013")
            pci = root / "sys/bus/pci/devices/0000:00:01.0"
            (pci / "device").write_text("0x00b8")
            (pci / "subsystem_vendor").write_text("0x1af4")
            (pci / "subsystem_device").write_text("0x1100")
            pci_display(root, 2, "0x1002")
            self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_no_display_or_unknown_pci_retains_chwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(TOOLS["virtual_display_profile"](root))
            pci_display(root, 1, "0x9999")
            self.assertIsNone(TOOLS["virtual_display_profile"](root))

    def test_step_is_removed_exactly_once_or_rejected(self):
        source = "sequence:\n- exec:\n  - partition\n  - chwd\n  - users\n"
        changed = TOOLS["omit_virtual_chwd_step"](source)
        self.assertNotIn("  - chwd\n", changed)
        self.assertIn("  - users\n", changed)
        for invalid in (source.replace("  - chwd", "  - chwd@other"),
                        source.replace("  - chwd\n", ""),
                        source + "  - chwd\n"):
            with self.assertRaises(ValueError):
                TOOLS["omit_virtual_chwd_step"](invalid)

    def test_installer_overrides_only_known_virtual_gpu(self):
        for vendor, bypass in (("0x1af4", True), ("0x15ad", True),
                               ("0x80ee", True), ("0x10de", False)):
            with self.subTest(vendor=vendor), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                branding.CalamaresBrandingChecks().make_fixture(root)
                pci_display(root, 1, vendor)
                original = root / "usr/share/calamares/settings_online.conf"
                original.write_text(original.read_text().replace(
                    "branding: cachyos",
                    "- exec:\n  - partition\n  - chwd\n  - users\nbranding: cachyos"))
                TOOLS["prepare"](root)
                settings = yaml.safe_load((root / "etc/calamares/settings.conf").read_text())
                self.assertEqual("chwd" not in settings["sequence"][1]["exec"], bypass)
                self.assertIn("users", settings["sequence"][1]["exec"])
                groups = yaml.safe_load((root / "etc/calamares/modules/netinstall.yaml").read_text())
                kde = next(item for item in groups if item["name"] == "KDE-Desktop")
                self.assertTrue(kde["selected"])
                self.assertTrue(kde["hidden"])
                self.assertEqual("mesa" in kde["packages"], bypass)
                self.assertEqual(kde["packages"].count("pyside6"), 1)
                # Settings regeneration remains idempotent.
                TOOLS["prepare"](root)
                settings2 = yaml.safe_load((root / "etc/calamares/settings.conf").read_text())
                self.assertEqual(settings, settings2)


if __name__ == "__main__":
    unittest.main()
