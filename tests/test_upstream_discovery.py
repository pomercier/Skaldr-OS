"""Offline, fail-closed tests for discovering the CachyOS upstream branch."""
from pathlib import Path
import os
import shlex
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "scripts/skaldr-discover-upstream.sh"
WORKFLOW = REPO / ".github/workflows/skaldr-upstream.yml"


class UpstreamBranchDiscoveryTests(unittest.TestCase):
    def invoke(self, output, exit_code=0):
        with tempfile.TemporaryDirectory() as temp:
            mock_git = Path(temp) / "git"
            mock_git.write_text(
                "#!/bin/sh\n"
                "if [ \"$1\" != '-c' ] || [ \"$2\" != 'protocol.version=2' ] "
                "|| [ \"$3\" != 'ls-remote' ] || [ \"$4\" != '--symref' ] "
                "|| [ \"$5\" != 'https://github.com/CachyOS/CachyOS-Live-ISO.git' ] "
                "|| [ \"$6\" != 'HEAD' ]; then exit 55; fi\n"
                "printf '%s\\n' " + shlex.quote(output) + "\n"
                f"exit {exit_code}\n"
            )
            mock_git.chmod(0o755)
            env = os.environ.copy()
            env["PATH"] = temp + os.pathsep + env["PATH"]
            return subprocess.run(
                ["bash", str(HELPER)], env=env,
                capture_output=True, text=True, timeout=10, check=False
            )

    def test_genuine_master_is_read_from_symbolic_head(self):
        output = ("ref: refs/heads/master\tHEAD\n"
                  "3215497d2e8c5fea90e185affcf973dfa2cf790b\tHEAD")
        result = self.invoke(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "master\n")

    def test_future_official_branch_rename_is_not_assumed(self):
        output = ("ref: refs/heads/main\tHEAD\n"
                  "0123456789012345678901234567890123456789\tHEAD")
        result = self.invoke(output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "main\n")

    def test_missing_symbolic_head_refuses_to_merge(self):
        result = self.invoke("3215497d2e8c5fea90e185affcf973dfa2cf790b\tHEAD")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("refusing upstream merge", result.stderr)

    def test_git_network_error_refuses_to_merge(self):
        result = self.invoke("upstream unavailable", 128)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("Cannot query", result.stderr)

    def test_invalid_branch_name_is_not_emitted(self):
        for ref in ("refs/tags/v1", "refs/heads/double..dot",
                    "refs/heads/master;danger", "refs/heads/a b",
                    "refs/heads/bad/"):
            with self.subTest(ref=ref):
                result = self.invoke("ref: " + ref + "\tHEAD")
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")

    def test_workflow_never_uses_unauthenticated_rest_api(self):
        content = WORKFLOW.read_text()
        self.assertIn("bash scripts/skaldr-discover-upstream.sh", content)
        self.assertNotIn("api.github.com/repos/CachyOS", content)
        self.assertIn("refs/remotes/cachyos/", content)
        self.assertIn("git merge --no-edit --no-ff", content)
        self.assertIn("git merge --abort", content)
        self.assertIn("git push origin HEAD:master", content)
        self.assertNotIn("git push --force", content)
        self.assertNotIn("git checkout -b", content)
        self.assertIn("python -m unittest discover", content)


if __name__ == "__main__":
    unittest.main()
