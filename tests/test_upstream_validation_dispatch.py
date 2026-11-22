"""Ensure upstream merges cannot silently bypass GitHub Actions ISO validation."""
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/skaldr-dispatch-upstream-validation.sh"
SHA = "a" * 40
OTHER = "b" * 40

FAKE_GIT = """#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
if args == ['rev-parse', 'HEAD']:
    print(os.environ['MOCK_LOCAL_SHA'])
elif args == ['ls-remote', '--exit-code', 'origin', 'refs/heads/master']:
    print(os.environ['MOCK_REMOTE_SHA'] + '\\trefs/heads/master')
else:
    print('unexpected git arguments: ' + repr(args), file=sys.stderr)
    sys.exit(3)
"""
FAKE_GH = """#!/usr/bin/env python3
import os, sys
args = sys.argv[1:]
with open(os.environ['MOCK_GH_CALLS'], 'a') as f:
    f.write(repr(args) + '\\n')
if args[:4] != ['api', '--silent', '-X', 'POST'] or args[-2:] != ['-f', 'ref=master']:
    sys.exit(4)
if os.environ.get('MOCK_GH_FAIL') and os.environ['MOCK_GH_FAIL'] in ' '.join(args):
    sys.exit(5)
"""


class UpstreamDispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.bin_dir = self.directory / "bin"
        self.bin_dir.mkdir()
        for name, content in (("git", FAKE_GIT), ("gh", FAKE_GH)):
            target = self.bin_dir / name
            target.write_text(content)
            target.chmod(0o755)
        self.calls = self.directory / "dispatch-calls.txt"
        self.environment = {
            **os.environ,
            "PATH": str(self.bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            "GITHUB_REPOSITORY": "pomercier/Skaldr-OS",
            "GH_TOKEN": "synthetic-test-token",
            "MOCK_LOCAL_SHA": SHA,
            "MOCK_REMOTE_SHA": SHA,
            "MOCK_GH_CALLS": str(self.calls),
        }

    def dispatch(self, *arguments, **changes):
        env = {**self.environment, **changes}
        return subprocess.run(["bash", str(SCRIPT), *arguments],
                              env=env, capture_output=True, text=True, check=False)

    def test_dispatches_both_jobs_after_matching_remote_and_local_sha(self):
        result = self.dispatch(SHA)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.calls.read_text().splitlines()
        self.assertEqual(len(calls), 2)
        self.assertIn("skaldr-checks.yml/dispatches", calls[0])
        self.assertIn("build.yml/dispatches", calls[1])
        self.assertIn("ref=master", calls[0])
        self.assertIn("ref=master", calls[1])

    def test_rejects_remote_branch_mismatch_without_dispatch(self):
        result = self.dispatch(SHA, MOCK_REMOTE_SHA=OTHER)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_rejects_local_branch_mismatch_without_dispatch(self):
        result = self.dispatch(SHA, MOCK_LOCAL_SHA=OTHER)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_rejects_wrong_repository_and_missing_token(self):
        self.assertNotEqual(self.dispatch(SHA, GITHUB_REPOSITORY="elsewhere/repo").returncode, 0)
        self.assertNotEqual(self.dispatch(SHA, GH_TOKEN="").returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_rejects_invalid_sha_without_dispatch(self):
        self.assertEqual(self.dispatch("master").returncode, 2)
        self.assertFalse(self.calls.exists())

    def test_failure_during_dispatch_never_reports_success(self):
        result = self.dispatch(SHA, MOCK_GH_FAIL="build.yml")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(len(self.calls.read_text().splitlines()), 2)

    def test_workflows_allow_action_dispatch_and_keep_verified_release_gates(self):
        upstream = (ROOT / ".github/workflows/skaldr-upstream.yml").read_text()
        automatic = (ROOT / ".github/workflows/skaldr-auto-verified-preview.yml").read_text()
        source = (ROOT / ".github/workflows/skaldr-checks.yml").read_text()
        build = (ROOT / ".github/workflows/build.yml").read_text()
        self.assertIn("actions: write", upstream)
        self.assertIn("steps.merge.outputs.changed == 'true'", upstream)
        self.assertIn("scripts/skaldr-dispatch-upstream-validation.sh", upstream)
        self.assertIn("workflow_dispatch", automatic)
        self.assertIn("head_branch == 'master'", automatic)
        self.assertIn("Verify real Calamares and cold-boot VM log evidence", automatic)
        self.assertIn("skaldr-dispatch-upstream-validation.sh", source)
        self.assertIn("workflow_dispatch:", source)
        self.assertIn("workflow_dispatch:", build)


if __name__ == "__main__":
    unittest.main()
