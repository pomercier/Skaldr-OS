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
            'losetup --find --show --offset "$offset" --sizelimit "$length" "$raw"',
            'sfdisk --json "$raw"',
            'Expected exactly one installed Btrfs partition',
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

    def test_synthetic_disk_rehearsal_is_isolated_and_real(self):
        smoke = ROOT / "scripts/skaldr-installed-rollback-image-smoke.sh"
        proc = subprocess.run(
            ["bash", "-n", str(smoke)], capture_output=True,
            text=True, timeout=10, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        env = os.environ.copy()
        env.pop("GITHUB_ACTIONS", None)
        env.pop("SKALDR_CI_INSTALLED_ROLLBACK", None)
        blocked = subprocess.run(
            ["bash", str(smoke)], env=env,
            capture_output=True, text=True, timeout=10, check=False,
        )
        self.assertEqual(blocked.returncode, 2)
        self.assertIn("Refusing image rehearsal", blocked.stderr)
        source = smoke.read_text()
        for item in (
            '[[ ! -e "$disk" && ! -L "$disk" ]]',
            'truncate -s 8G "$raw"',
            'sfdisk "$raw"',
            'losetup --find --show --offset "$((264192 * 512))"',
            'mkfs.btrfs -f -m single -d single',
            'qemu-img convert -S 4k -O qcow2 "$raw" "$disk"',
            'bash scripts/skaldr-ci-installed-rollback.sh "$disk"',
            '"original-before-rollback"',
            '"modified-after-snapshot"',
            'btrfs property get -ts',
            'Numeric Btrfs rootflags detected',
            '[[ "$before" == "$after" ]]',
            'default_id=',
            'root_id=',
        ):
            self.assertIn(item, source)
        self.assertNotIn('mkfs.btrfs /dev/', source)
        self.assertNotIn('qemu-img convert -O raw /dev/', source)

    def test_synthetic_rehearsal_workflow_keeps_real_iso_ci_separate(self):
        wf = (ROOT / ".github/workflows/skaldr-installed-rollback-image.yml").read_text()
        self.assertIn("image: archlinux:base-devel", wf)
        self.assertIn("options: --privileged", wf)
        self.assertIn("SKALDR_CI_INSTALLED_ROLLBACK: disposable-calamares-qcow2", wf)
        self.assertIn("bash scripts/skaldr-installed-rollback-image-smoke.sh", wf)
        self.assertNotIn("workflow_run:", wf)
        self.assertNotIn("release:", wf)

    def test_reused_validated_iso_probe_is_not_a_release_gate(self):
        workflow = (
            ROOT / ".github/workflows/skaldr-installed-rollback-probe.yml"
        ).read_text()
        for required in (
            "run-id: 43745598535",
            "skaldr-os-x86_64-261115",
            "sha256sum --check SHA256SUMS",
            'TEST_BOOTLOADER: "limine"',
            'TEST_FILESYSTEM: "btrfs"',
            "test_install_calamares cachyos dailylive",
            "SKALDR_CI_INSTALLED_ROLLBACK",
        ):
            # Authorization is established inside the called helper;
            # the Quicktest wrapper executes the authorized helper.
            if required == "SKALDR_CI_INSTALLED_ROLLBACK":
                self.assertIn(required, SCRIPT.read_text())
            else:
                self.assertIn(required, workflow)
        self.assertNotIn("gh release", workflow)
        self.assertNotIn("workflow_run:", workflow)

    def test_workflow_depends_on_real_qemu_and_btrfs_tools(self):
        workflow = WORKFLOW.read_text()
        self.assertIn('qemu-desktop socat btrfs-progs', workflow)
        self.assertIn('TEST_BOOTLOADER: "${{ matrix.bootloader }}"', workflow)
        self.assertIn('TEST_FILESYSTEM: "${{ matrix.filesystem }}"', workflow)
        self.assertIn('QT_TESTCASES_DIR: "./testcases"', workflow)
        self.assertNotIn("SKIP_ROLLBACK", workflow)


if __name__ == "__main__":
    unittest.main()
