"""Safety-focused unit tests for opt-in Skaldr controls."""
from pathlib import Path
import json
import os
import runpy
import subprocess
import tempfile
import unittest
from unittest.mock import patch

LIVE = Path(__file__).resolve().parents[1] / "archiso/airootfs"
UPDATE = LIVE / "usr/local/bin/skaldr-update"
PERFORMANCE = LIVE / "usr/local/bin/skaldr-performance"
REPORT = LIVE / "usr/local/bin/skaldr-report"


class Result:
    def __init__(self, code=0, output=""):
        self.returncode, self.stdout = code, output


class UpdateSafetyTests(unittest.TestCase):
    def setUp(self):
        self.ns = runpy.run_path(str(UPDATE), run_name="safe_test")

    def test_non_btrfs_requires_specific_explicit_opt_in(self):
        policy = self.ns["snapshot_required"]
        for fs in ("ext4", "xfs", "unknown", "zfs"):
            with self.subTest(fs=fs):
                with self.assertRaisesRegex(RuntimeError, "without-snapshot"):
                    policy(fs, False)
                self.assertFalse(policy(fs, True))
        self.assertTrue(policy("btrfs", False))
        self.assertTrue(policy("btrfs", True))  # Opt-in cannot bypass Btrfs safety.

    def test_root_fs_probe_and_failure(self):
        fs = self.ns["filesystem"]
        self.assertEqual(fs(lambda cmd, **kw: Result(0, "btrfs\n")), "btrfs")
        with self.assertRaisesRegex(RuntimeError, "Cannot determine"):
            fs(lambda cmd, **kw: Result(1, ""))

    def test_snapshot_failure_is_fail_closed(self):
        snap = self.ns["snapshot"]
        commands = []
        def fake(args, **kw):
            commands.append(args)
            if "get-config" in args:
                return Result(0)
            return Result(1)
        with patch.dict(snap.__globals__, {"shutil": type("Util", (), {"which": staticmethod(lambda x: x)})}):
            with self.assertRaisesRegex(RuntimeError, "pacman was NOT executed"):
                snap(execute_fn=fake)
        self.assertEqual(len(commands), 2)
        self.assertEqual(commands[0][-1], "get-config")
        self.assertEqual(commands[1][0], "snapper")

    def test_dry_run_never_calls_pacman(self):
        main = self.ns["main"]
        calls = []
        def no_exec(args, **kw):
            calls.append(args)
            return Result(0, "ext4\n")
        with patch.dict(main.__globals__, {"execute": no_exec, "filesystem": lambda: "ext4"}):
            self.assertEqual(main(["--dry-run", "--allow-without-snapshot"]), 0)
        self.assertFalse(calls)

    def test_requires_root_before_pacman(self):
        main = self.ns["main"]
        with patch.dict(main.__globals__, {"filesystem": lambda: "ext4"}):
            with patch("os.geteuid", return_value=1000):
                with self.assertRaisesRegex(RuntimeError, "administrative"):
                    main(["--apply", "--allow-without-snapshot"])

    def test_no_forced_yes_or_signature_bypass(self):
        text = UPDATE.read_text()
        self.assertIn('["pacman", "-Syu"]', text)
        self.assertNotIn("--noconfirm", text)
        self.assertNotIn("--overwrite", text)
        self.assertNotIn("--disable-download-timeout", text)


class PerformanceSafetyTests(unittest.TestCase):
    def setUp(self):
        self.ns = runpy.run_path(str(PERFORMANCE), run_name="safe_test")

    def test_default_and_atomic_storage(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "performance-profile"
            current = self.ns["current"]
            store = self.ns["store"]
            self.assertEqual(current(path), "gaming")
            for name in ("balanced", "gaming", "creator"):
                store(name, directory=Path(d))
                self.assertEqual(current(path), name)
                self.assertEqual(path.stat().st_mode & 0o777, 0o644)
            path.write_text("unknown\n")
            with self.assertRaisesRegex(ValueError, "Invalid"):
                current(path)

    def test_plan_requires_no_elevation_or_changes(self):
        main = self.ns["main"]
        for name in ("balanced", "gaming", "creator"):
            self.assertEqual(main(["plan", name]), 0)
        with patch("os.geteuid", return_value=1000):
            with self.assertRaises(PermissionError):
                main(["apply", "gaming", "--confirm"])

    def test_creator_does_not_make_undocumented_overclock_claim(self):
        self.assertEqual(self.ns["PROFILES"]["creator"], "performance")
        script = PERFORMANCE.read_text()
        self.assertNotIn("nvidia-smi -pl", script)
        self.assertNotIn("lactd set", script)


class ReportPrivacyTests(unittest.TestCase):
    def setUp(self):
        self.ns = runpy.run_path(str(REPORT), run_name="safe_test")

    def test_whitelist_removes_sensitive_context(self):
        src = {"kernel": "linux-cachyos", "hostname": "private-pc",
               "username": "private-user", "ip_address": "192.0.2.1",
               "disk_serial": "secret", "gpu": ["Intel GPU"],
               "root_filesystem": "btrfs"}
        safe = self.ns["sanitize"](src)
        for secret in ("hostname", "username", "ip_address", "disk_serial"):
            self.assertNotIn(secret, safe)
        self.assertIn("kernel", safe)
        self.assertIn("privacy_note", safe)

    def test_private_file_and_no_overwriting_or_symlinks(self):
        with tempfile.TemporaryDirectory() as d:
            writer = self.ns["write_new"]
            dest = Path(d) / "report.json"
            writer(dest, '{"safe": true}\n')
            self.assertEqual(dest.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                writer(dest, "overwrite")
            link = Path(d) / "linked.json"
            link.symlink_to(dest)
            with self.assertRaises(ValueError):
                writer(link, "tamper")
            self.assertIn("safe", dest.read_text())

    def test_no_automatic_remote_upload(self):
        body = REPORT.read_text()
        for forbidden in ("paste.cachyos.org", "requests.post(", "curl ", "scp "):
            self.assertNotIn(forbidden, body)


class InstalledIntegrationTests(unittest.TestCase):
    def test_reach_all_three_tools_from_live_and_installed_center(self):
        center = (LIVE / "usr/local/bin/skaldr-center").read_text()
        install = (LIVE / "usr/local/bin/skaldr-cal-inject").read_text()
        perms = (Path(__file__).resolve().parents[1] / "archiso/profiledef.sh").read_text()
        for name in ("skaldr-report", "skaldr-update", "skaldr-performance"):
            with self.subTest(tool=name):
                self.assertIn(name, center)
                self.assertIn("/usr/local/bin/" + name, install)
                self.assertIn(f'["/usr/local/bin/{name}"]="0:0:755"', perms)
        self.assertIn("kdialog --title 'Skaldr OS update' --yesno", center)
        self.assertIn("pkexec /usr/local/bin/skaldr-update --apply", center)
        self.assertIn("pkexec /usr/local/bin/skaldr-performance apply", center)
        runtime = (LIVE / "usr/local/bin/skaldr-profile").read_text()
        self.assertIn('Path("/etc/skaldr/performance-profile")', runtime)


if __name__ == "__main__":
    unittest.main()
