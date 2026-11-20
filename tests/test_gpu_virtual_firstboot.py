"""Standalone behavior regression tests for the Skaldr first-login GPU assistant."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "archiso/airootfs/usr/local/bin/skaldr-gpu-assistant"

VIRTIO = '00:01.0 VGA compatible controller [0300]: Red Hat, Inc. Virtio 1.0 GPU [1af4:1050] (rev 01)'
VMSVGA = '00:02.0 VGA compatible controller [0300]: VMware SVGA II Adapter [15ad:0405] (rev 02)'
PHYSICAL = '01:00.0 VGA compatible controller [0300]: NVIDIA Corporation GA102 [GeForce RTX 3080] [10de:2216]'
AMD = '01:00.0 VGA compatible controller [0300]: Advanced Micro Devices, Inc. Navi 22 [1002:73df]'
CIRRUS = '00:01.0 VGA compatible controller [0300]: Cirrus Logic GD 5446 [1013:00b8]'

class GpuAssistantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.home = self.root / 'home'
        self.bin.mkdir()
        self.home.mkdir()
        commands = {
            'lspci': '#!/bin/sh\nprintf "%s\\n" "$TEST_PCI"\n',
            'chwd': '#!/bin/sh\nif [ "${1:-}" = "--list" ]; then echo nouveau; else echo "CHWD:$*" >> "$TEST_ACTIONS"; fi\n',
            'kdialog': '#!/bin/sh\nprintf "%s\\n" "KDIALOG:$*" >> "$TEST_ACTIONS"\ncase "$*" in *--menu*) echo keep;; esac\n',
            'pkexec': '#!/bin/sh\nprintf "%s\\n" "PKEXEC:$*" >> "$TEST_ACTIONS"\n',
        }
        for name, content in commands.items():
            dest = self.bin / name
            dest.write_text(content)
            dest.chmod(0o755)

    def invoke(self, devices, *args):
        actions = self.root / 'actions'
        if actions.exists(): actions.unlink()
        env = os.environ | {
            'PATH': f'{self.bin}:' + os.environ['PATH'],
            'HOME': str(self.home),
            'TEST_PCI': devices,
            'TEST_ACTIONS': str(actions),
        }
        p = subprocess.run(['bash', str(SCRIPT), *args], env=env, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        return actions.read_text() if actions.exists() else ''

    def marker(self):
        return (self.home / '.config/skaldr/gpu-choice-complete').exists()

    def test_virtio_vm_skips_popup(self):
        self.assertEqual(self.invoke(VIRTIO), '')
        self.assertTrue(self.marker())

    def test_vmsvga_vm_skips_popup(self):
        self.assertEqual(self.invoke(VMSVGA), '')
        self.assertTrue(self.marker())

    def test_multiple_virtual_displays_skip_popup(self):
        self.assertEqual(self.invoke(VIRTIO + '\n' + VMSVGA), '')
        self.assertTrue(self.marker())

    def test_gpu_passthrough_never_skips_popup(self):
        self.assertIn('KDIALOG:', self.invoke(VIRTIO + '\n' + PHYSICAL))

    def test_physical_nvidia_retains_dialog(self):
        self.assertIn('KDIALOG:', self.invoke(PHYSICAL))
        self.assertTrue(self.marker())

    def test_physical_amd_retains_dialog(self):
        self.assertIn('KDIALOG:', self.invoke(AMD))

    def test_cirrus_not_assumed_virtual(self):
        self.assertIn('KDIALOG:', self.invoke(CIRRUS))

    def test_recheck_explicitly_shows_dialog(self):
        self.assertEqual(self.invoke(VIRTIO), '')
        self.assertIn('KDIALOG:', self.invoke(VIRTIO, '--recheck'))

    def test_normal_autostart_not_reprompt_after_completion(self):
        self.assertEqual(self.invoke(VIRTIO), '')
        self.assertEqual(self.invoke(PHYSICAL), '')

    def test_non_display_pci_does_not_prompt(self):
        self.assertEqual(self.invoke('00:01.0 Network controller: Intel [8086:100e]'), '')
        self.assertFalse(self.marker())

if __name__ == '__main__':
    unittest.main()
