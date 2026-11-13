"""Isolated Calamares integration regression tests.

Use real YAML parsing on disposable configuration files. These checks do not
replace booting the packaged Calamares installer in the ISO test matrix.
"""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import yaml


INJECT = (Path(__file__).resolve().parents[1]
          / "archiso/airootfs/usr/local/bin/skaldr-cal-inject")
POSTINSTALL = "/usr/local/bin/skaldr-postinstall"


class CalamaresInjectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skaldr-cal-inject-")
        self.root = Path(self.temp.name)
        self.pacstrap = self.root / "pacstrap.conf"
        self.shellprocess = self.root / "shellprocess.conf"

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self):
        env = dict(os.environ, SKALDR_CALAMARES_MODULES=str(self.root))
        return subprocess.run([sys.executable, str(INJECT)], env=env,
                              capture_output=True, text=True, check=False)

    def test_preserves_existing_modules_and_is_idempotent(self):
        self.pacstrap.write_text(
            '---\nbasePackages:\n  - base\npostInstallFiles:\n'
            '  - "/etc/mkinitcpio.conf"\n')
        self.shellprocess.write_text(
            '---\ndontChroot: false\nscript:\n'
            '    - command: "/usr/local/bin/dmcheck"\n'
            'i18n:\n  name: "Cleanup"\n')
        first = self.invoke()
        self.assertEqual(first.returncode, 0, first.stderr)
        pacstrap_yaml = yaml.safe_load(self.pacstrap.read_text())
        process_yaml = yaml.safe_load(self.shellprocess.read_text())
        self.assertIn("/etc/mkinitcpio.conf", pacstrap_yaml["postInstallFiles"])
        self.assertEqual(pacstrap_yaml["postInstallFiles"].count(POSTINSTALL), 1)
        self.assertNotIn("/etc/skel/.config/kcminputrc",
                         pacstrap_yaml["postInstallFiles"])
        commands = [step["command"] for step in process_yaml["script"]]
        self.assertEqual(commands, ["/usr/local/bin/dmcheck", POSTINSTALL])
        self.assertEqual(process_yaml["script"][-1]["timeout"], 3600)
        self.assertTrue(process_yaml["script"][-1]["verbose"])
        self.assertEqual(process_yaml["i18n"]["name"], "Cleanup")
        before = (self.pacstrap.read_bytes(), self.shellprocess.read_bytes())
        second = self.invoke()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(before, (self.pacstrap.read_bytes(),
                                  self.shellprocess.read_bytes()))

    def test_invalid_shellprocess_does_not_partially_update_pacstrap(self):
        original_pacstrap = ('postInstallFiles:\n'
                            '  - "/etc/mkinitcpio.conf"\n')
        original_shellprocess = 'script: []\n'
        self.pacstrap.write_text(original_pacstrap)
        self.shellprocess.write_text(original_shellprocess)
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing Calamares key: script", result.stderr)
        self.assertEqual(self.pacstrap.read_text(), original_pacstrap)
        self.assertEqual(self.shellprocess.read_text(), original_shellprocess)

    def test_nested_key_is_not_mistaken_for_root_section(self):
        original = ('module:\n'
                    '  postInstallFiles:\n'
                    '    - "/etc/mkinitcpio.conf"\n')
        self.pacstrap.write_text(original)
        self.shellprocess.write_text('script:\n  - command: "echo ok"\n')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Missing Calamares key: postInstallFiles", result.stderr)
        self.assertEqual(self.pacstrap.read_text(), original)

    def test_comments_do_not_suppress_required_hooks(self):
        self.pacstrap.write_text(
            'postInstallFiles:\n'
            '  # "/usr/local/bin/skaldr-postinstall"\n'
            '  - "/etc/mkinitcpio.conf"\n')
        self.shellprocess.write_text(
            'script:\n'
            '  # command: "/usr/local/bin/skaldr-postinstall"\n'
            '  - command: "/usr/local/bin/dmcheck"\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        pacstrap_yaml = yaml.safe_load(self.pacstrap.read_text())
        process_yaml = yaml.safe_load(self.shellprocess.read_text())
        self.assertEqual(pacstrap_yaml["postInstallFiles"].count(POSTINSTALL), 1)
        self.assertEqual([step["command"] for step in process_yaml["script"]]
                         .count(POSTINSTALL), 1)

    def test_missing_required_file_refuses_installation(self):
        self.pacstrap.write_text('postInstallFiles:\n  - "/etc/example"\n')
        result = self.invoke()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Required Calamares configuration missing", result.stderr)


if __name__ == "__main__":
    unittest.main()
