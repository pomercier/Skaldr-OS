"""Keep real QEMU guest root tests isolated from installed machine disks."""
from pathlib import Path
import os
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-qemu-root-recovery-smoke.sh"
WORKFLOW = ROOT / ".github/workflows/skaldr-qemu-root-recovery.yml"


class QemuRootRecoveryTests(unittest.TestCase):
    def test_shell_syntax(self):
        done = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True,
                              text=True, timeout=10, check=False)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_refuses_run_outside_disposable_ci(self):
        env = os.environ.copy()
        env.pop("GITHUB_ACTIONS", None)
        env.pop("SKALDR_QEMU_CI_EXPLICIT", None)
        done = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True,
                              text=True, timeout=10, check=False)
        self.assertEqual(done.returncode, 2)
        self.assertIn("Refusing QEMU recovery test", done.stderr)

    def test_device_formatting_is_limited_to_new_scratch_image(self):
        source = SCRIPT.read_text()
        self.assertIn('workdir="$(mktemp -d "${RUNNER_TEMP%/}/skaldr-qemu-root-ci.', source)
        self.assertIn('image="$workdir/disposable-root.img"', source)
        self.assertIn('[[ "$image" == "$workdir/disposable-root.img" && ! -e "$image" ]]', source)
        self.assertIn('mkfs.btrfs -f -m single -d single "$image"', source)
        self.assertNotIn('mkfs.btrfs /dev/', source)
        self.assertNotIn('btrfs subvolume set-default "$restored_id" /', source)
        self.assertNotIn('grub-mkconfig', source)
        self.assertNotIn('limine-update', source)

    def test_both_real_kernel_boots_are_required(self):
        source = SCRIPT.read_text()
        for required in (
            'mkinitcpio --kernel "$kver"',
            'qemu-system-x86_64',
            '-machine accel=tcg',
            '-kernel "$kernel" -initrd "$initrd"',
            'rootflags=subvol=@',
            'boot_uefi_guest "explicit" "modified-after-snapshot"',
            'boot_uefi_guest "restored" "original-before-snapshot"',
            "OVMF_CODE.4m.fd",
            "OVMF_VARS.4m.fd",
            "if=pflash,format=raw,readonly=on",
            'grub-mkrescue -o "$iso"',
            'boot_grub_guest "explicit rootflags"',
            'boot_grub_guest "restored default root"',
            '"modified-after-snapshot" "$log_dir/explicit-root.log"',
            '"original-before-snapshot" "$log_dir/restored-root.log"',
            'SKALDR_QEMU_ROOT_STATE=',
            'btrfs subvolume snapshot -r "$root" "$mnt/@snapshot"',
            'btrfs subvolume snapshot "$mnt/@snapshot" "$mnt/@restored"',
            'btrfs subvolume set-default "$restored_id" "$mnt"',
            'NOT TESTED: full installed KDE',
        ):
            self.assertIn(required, source)

    def test_workflow_isolated_and_not_an_iso_release(self):
        workflow = WORKFLOW.read_text()
        self.assertIn("image: archlinux:base-devel", workflow)
        self.assertIn("options: --privileged", workflow)
        self.assertIn("SKALDR_QEMU_CI_EXPLICIT: disposable-qemu-root-image", workflow)
        self.assertIn("qemu-system-x86", workflow)
        self.assertIn("linux mkinitcpio", workflow)
        self.assertIn("grub xorriso mtools dosfstools edk2-ovmf", workflow)
        self.assertNotIn("git push", workflow)
        self.assertNotIn("release:", workflow)
        self.assertNotIn("workflow_run:", workflow)


if __name__ == "__main__":
    unittest.main()
