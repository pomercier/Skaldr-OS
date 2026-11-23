"""Regression tests for deterministic, KDE-first display manager selection.

Run the real dmcheck Bash script with mock pacman/ln/rm commands. No system
files are altered; checks cover ordering and the single-manager invariant.
"""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "archiso/airootfs/usr/local/bin/dmcheck"
)


class DisplayManagerSelectionTests(unittest.TestCase):
    def run_dmcheck(self, installed):
        with tempfile.TemporaryDirectory(prefix="skaldr-dmcheck-") as directory:
            root = Path(directory)
            for name, code in {
                "pacman": (
                    "#!/bin/sh\n"
                    "[ \"$1\" = \"-Q\" ] || exit 2\n"
                    "case \" $SKALDR_MOCK_PACKAGES \" in\n"
                    "  *\" $2 \"*) exit 0 ;;\n"
                    "esac\n"
                    "exit 1\n"
                ),
                "ln": (
                    "#!/bin/sh\n"
                    "printf 'ln %s %s\\n' \"$2\" \"$3\" >> \"$SKALDR_MOCK_LOG\"\n"
                ),
                "rm": (
                    "#!/bin/sh\n"
                    "printf 'rm %s\\n' \"$2\" >> \"$SKALDR_MOCK_LOG\"\n"
                ),
            }.items():
                mock = root / name
                mock.write_text(code, encoding="utf-8")
                mock.chmod(0o755)
            log = root / "operations.log"
            env = os.environ.copy()
            env.update(
                PATH=f"{root}{os.pathsep}{os.environ.get('PATH', '')}",
                SKALDR_MOCK_PACKAGES=" ".join(installed),
                SKALDR_MOCK_LOG=str(log),
            )
            result = subprocess.run(
                ["bash", str(SCRIPT)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return log.read_text(encoding="utf-8").splitlines() if log.exists() else []

    def test_plasma_login_manager_takes_priority_over_sddm(self):
        self.assertEqual(
            self.run_dmcheck(["sddm", "plasma-login-manager", "gdm"]),
            ["ln /usr/lib/systemd/system/plasmalogin.service /etc/systemd/system/display-manager.service"],
        )

    def test_sddm_is_kde_fallback(self):
        self.assertEqual(
            self.run_dmcheck(["sddm", "gdm"]),
            ["ln /usr/lib/systemd/system/sddm.service /etc/systemd/system/display-manager.service"],
        )

    def test_ly_removes_tty2_getty_only_when_selected(self):
        self.assertEqual(
            self.run_dmcheck(["ly", "gdm"]),
            [
                "rm /etc/systemd/system/getty.target.wants/getty@tty2.service",
                "ln /usr/lib/systemd/system/ly@.service /etc/systemd/system/multi-user.target.wants/ly@tty2.service",
            ],
        )

    def test_no_manager_installed_does_not_touch_systemd(self):
        self.assertEqual(self.run_dmcheck([]), [])


if __name__ == "__main__":
    unittest.main()
