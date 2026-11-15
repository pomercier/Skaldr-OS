"""Protect real disks and preserve real scratch-Btrfs recovery assertions."""
from pathlib import Path
import os
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-btrfs-recovery-smoke.sh"
WORKFLOW = ROOT / ".github/workflows/skaldr-btrfs-recovery.yml"


class BtrfsRecoverySmokeTests(unittest.TestCase):
    def test_shell_script_is_syntactically_valid(self):
        result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True,
                                text=True, check=False, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_script_refuses_unapproved_execution_without_disk_changes(self):
        env = os.environ.copy()
        env.pop("SKALDR_BTRFS_CI_EXPLICIT", None)
        env.pop("GITHUB_ACTIONS", None)
        result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True,
                                text=True, check=False, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Refusing recovery test", result.stderr)

    def test_format_target_is_only_newly_created_temporary_image(self):
        source = SCRIPT.read_text()
        self.assertIn('mktemp -d "${RUNNER_TEMP%/}/skaldr-btrfs-ci.', source)
        self.assertIn('image="$workdir/disposable.img"', source)
        self.assertIn('[[ "$image" == "$workdir/disposable.img" && ! -e "$image" ]]', source)
        self.assertIn('mkfs.btrfs -f -m single -d single "$image"', source)
        self.assertNotIn('mkfs.btrfs /dev/', source)
        self.assertNotIn('mount /dev/', source)
        self.assertNotIn("snapper rollback", source)
        self.assertNotIn("btrfs subvolume set-default", source)
        self.assertNotIn("grub-mkconfig", source)

    def test_real_snapper_and_data_recovery_are_mandatory(self):
        source = SCRIPT.read_text()
        for line in (
            'snapper --no-dbus -c "$config" create-config',
            'snapper --no-dbus -c "$config" get-config',
            'snapper --no-dbus -c "$config" create --type single',
            'btrfs property get -ts "$snapshot" ro',
            'btrfs subvolume snapshot "$snapshot" "$mnt/@restored-test"',
            'cmp -s "$snapshot/state.txt" "$mnt/@restored-test/state.txt"',
            'modified-after-snapshot',
        ):
            self.assertIn(line, source)

    def test_ci_runs_in_privileged_disposable_container_only(self):
        content = WORKFLOW.read_text()
        self.assertIn("image: archlinux:base-devel", content)
        self.assertIn("options: --privileged", content)
        self.assertIn("SKALDR_BTRFS_CI_EXPLICIT: disposable-ci-image", content)
        self.assertIn("bash scripts/skaldr-btrfs-recovery-smoke.sh", content)
        self.assertIn("snapper", content)
        self.assertIn("btrfs-progs", content)
        self.assertNotIn("git push", content)
        self.assertNotIn("workflow_run:", content)


if __name__ == "__main__":
    unittest.main()
