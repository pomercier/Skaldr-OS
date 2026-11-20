"""Prevent rolling-repository 404s during Calamares pacstrap installations.

The signed package databases inside an ISO can be older than available
rolling-kernel packages. Preflight must refresh metadata before disk changes.
"""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "archiso/airootfs/usr/local/bin/calamares-online.sh"


class CalamaresRepositoryRefreshTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SCRIPT.read_text(encoding="utf-8")
        start = cls.source.index('stage="refresh live package databases"')
        end = cls.source.index('stage="start Calamares GUI"', start)
        cls.block = cls.source[start:end]

    def invoke(self, should_fail=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sudo = root / "sudo"
            actions = root / "actions"
            sudo.write_text(
                '#!/bin/sh\nprintf "%s\\n" "$*" >> "$MOCK_ACTIONS"\n'
                'exit "$MOCK_SUDO_EXIT"\n', encoding="utf-8")
            sudo.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "PATH": str(root) + os.pathsep + env.get("PATH", ""),
                "MOCK_ACTIONS": str(actions),
                "MOCK_SUDO_EXIT": "42" if should_fail else "0",
            })
            command = "set -Eeuo pipefail\n" + self.block + "\nprintf 'GUI_LAUNCHED\\n'\n"
            proc = subprocess.run(
                ["bash", "-c", command], env=env,
                capture_output=True, text=True, timeout=12, check=False)
            return proc, actions.read_text() if actions.exists() else ""

    def test_shell_syntax(self):
        result = subprocess.run(["bash", "-n", str(SCRIPT)], capture_output=True,
                                text=True, check=False, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_refresh_after_installer_preparation_before_gui(self):
        self.assertLess(self.source.index("sudo /usr/local/bin/skaldr-cal-inject"),
                        self.source.index("sudo pacman -Syy --noconfirm"))
        self.assertLess(self.source.index("sudo pacman -Syy --noconfirm"),
                        self.source.index("pkexec-wrapper calamares -D6"))

    def test_success_invokes_only_repository_refresh(self):
        proc, commands = self.invoke()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(commands.strip(), "pacman -Syy --noconfirm")
        self.assertIn("Repository metadata refreshed successfully", proc.stdout)
        self.assertIn("GUI_LAUNCHED", proc.stdout)

    def test_failed_refresh_prevents_installer_start(self):
        proc, commands = self.invoke(should_fail=True)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(commands.strip(), "pacman -Syy --noconfirm")
        self.assertNotIn("GUI_LAUNCHED", proc.stdout)
        self.assertIn("installation was NOT started", proc.stderr)

    def test_never_installs_or_upgrades_live_packages(self):
        self.assertIn("sudo pacman -Syy --noconfirm", self.block)
        for forbidden in ("pacman -Syu", "pacman -Sy --needed", "pacman -U",
                          "--overwrite", "--nodeps", "--assume-installed"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.block)

    def test_never_weakens_signature_verification(self):
        for forbidden in ("SigLevel", "TrustAll", "--skippgpcheck", "--nosignature",
                          "pacman-key --init", "rm -rf /etc/pacman.d/gnupg"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.block)


if __name__ == "__main__":
    unittest.main()
