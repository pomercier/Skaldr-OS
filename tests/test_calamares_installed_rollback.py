"""Guard genuine disposable Calamares rollback integration in Quicktest."""
from pathlib import Path
import os
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-ci-installed-rollback.sh"
INSTALL_TEST = ROOT / "testcases/cachyos/dailylive/test_install_calamares"
WORKFLOW = ROOT / ".github/workflows/build.yml"


class CalamaresInstalledRollbackTests(unittest.TestCase):
    def test_scripts_pass_bash_syntax(self):
        for target in (SCRIPT, INSTALL_TEST):
            result = subprocess.run(
                ["bash", "-n", str(target)], capture_output=True,
                text=True, timeout=10, check=False,
            )
            self.assertEqual(result.returncode, 0, f"{target}: {result.stderr}")

    def test_refuses_outside_disposable_ci_before_disk_access(self):
        env = os.environ.copy()
        env.pop("GITHUB_ACTIONS", None)
        env.pop("SKALDR_CI_INSTALLED_ROLLBACK", None)
        result = subprocess.run(
            ["bash", str(SCRIPT), "/dev/sda"], env=env,
            capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Refusing installed rollback", result.stderr)

    def test_helper_restricts_disk_and_keeps_original_until_validated(self):
        source = SCRIPT.read_text()
        for required in (
            'SKALDR_CI_INSTALLED_ROLLBACK:-',
            'disposable-calamares-qcow2',
            'expected="$workspace/machines/cachyos-dailylive/disk.qcow2"',
            '[[ "$disk" == "$expected" && -f "$disk" && ! -L "$disk"',
            'qemu-img info --output=json "$disk"',
            'qemu-img convert -S 4k -O raw "$disk" "$raw"',
            'losetup --find --show --partscan "$raw"',
            'mount -t btrfs -o subvolid=5',
            'btrfs subvolume snapshot -r "$root"',
            'btrfs subvolume snapshot "$top/@skaldr-ci-source-snapshot"',
            'btrfs subvolume set-default "$id" "$top"',
            'qemu-img check "$restored"',
            'mv "$disk" "$scratch/unmodified-install.qcow2"',
            'mv "$restored" "$disk"',
            "original-before-rollback",
            "modified-after-snapshot",
            "ro=true",
            "NOT YET VERIFIED: bootloader, KDE or VM reboot",
        ):
            self.assertIn(required, source)
        for forbidden in (
            'mkfs.btrfs /dev/', 'mkfs.ext4 /dev/',
            'btrfs subvolume delete "$root"',
            'grub-mkconfig', 'limine-update', 'pacman -Syu',
        ):
            self.assertNotIn(forbidden, source)

    def test_quicktest_runs_only_after_real_install_and_kde(self):
        content = INSTALL_TEST.read_text()
        self.assertIn('function test_installed_btrfs_snapshot_rollback()', content)
        self.assertIn('"${TEST_BOOTLOADER:-}" != "limine"', content)
        self.assertIn('"${TEST_FILESYSTEM:-}" != "btrfs"', content)
        self.assertIn('bash scripts/skaldr-ci-installed-rollback.sh', content)
        self.assertIn('if grep -aFq \'.iso\' "/proc/$qemu_pid/cmdline"', content)
        self.assertIn('konsole --hold -e cat /etc/skaldr-ci-rollback-state', content)
        self.assertIn('"original-before-rollback" 20 5', content)
        self.assertIn('"System overview" 18 6', content)
        order = (
            "    test_installed_system_cold_boot\n"
            "    test_installed_plasma_first_login\n"
            "    test_installed_native_control_center\n"
            "    test_installed_btrfs_snapshot_rollback\n"
            "    test_power_off_vm"
        )
        self.assertIn(order, content)

    def test_workflow_depends_on_real_qemu_and_btrfs_tools(self):
        workflow = WORKFLOW.read_text()
        self.assertIn('qemu-desktop socat btrfs-progs', workflow)
        self.assertIn('TEST_BOOTLOADER: "${{ matrix.bootloader }}"', workflow)
        self.assertIn('TEST_FILESYSTEM: "${{ matrix.filesystem }}"', workflow)
        self.assertIn('QT_TESTCASES_DIR: "./testcases"', workflow)
        self.assertNotIn("SKIP_ROLLBACK", workflow)


if __name__ == "__main__":
    unittest.main()
