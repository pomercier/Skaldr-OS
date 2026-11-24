"""Fail-closed automatic preview regression tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/skaldr-auto-verified-preview.yml"


class AutoPreviewGateTests(unittest.TestCase):
    def test_catchup_is_workflow_only_and_requires_success(self):
        source = WORKFLOW.read_text()
        self.assertIn("push:\n    branches: [master]\n    paths:\n      - '.github/workflows/skaldr-auto-verified-preview.yml'", source)
        self.assertIn("github.event_name == 'push'", source)
        self.assertIn("status=success&per_page=30", source)
        self.assertIn('echo "SOURCE_SHA=$selected_sha" >> "$GITHUB_ENV"', source)
        self.assertIn('git merge-base --is-ancestor "$SOURCE_SHA" HEAD', source)
        self.assertIn('Skip stale build; untested source change:', source)

    def test_docs_only_changes_may_follow_a_successful_iso(self):
        source = WORKFLOW.read_text()
        self.assertIn("README.md|docs/**|.github/workflows/skaldr-auto-verified-preview.yml|.github/workflows/skaldr-release.yml)", source)
        for risky in ("archiso/**|", "scripts/**|", "testcases/**|", "VERSION|"):
            self.assertNotIn(risky, source)

    def test_all_six_vm_jobs_and_bios_installed_logs_required(self):
        source = WORKFLOW.read_text()
        for text in ("Testing (grub / ext4)", "Testing (limine / btrfs)",
                     "Testing (bios / live)", "Testing (grub-bios / ext4)",
                     "Verify full-size ISO preview reconstruction"):
            self.assertIn(text, source)
        self.assertIn("Verified 6/6 real ISO", source)
        self.assertIn("for flavor in grub-ext4 limine-btrfs grub-bios-ext4", source)
        self.assertIn("Boot actual Syslinux live ISO through legacy BIOS", source)
        self.assertIn("Log into the installed Plasma session with the test account", source)
        self.assertIn("Cold boot the newly installed system, without the live ISO", source)
        self.assertIn("all(job['conclusion']=='success' for job in jobs)", source)

    def test_never_auto_promotes_stable_or_release_mode(self):
        source = WORKFLOW.read_text()
        self.assertIn('inputs.get("release_mode", "false")', source)
        self.assertIn("gh workflow run skaldr-release.yml", source)
        self.assertIn("--field stable=false", source)


if __name__ == "__main__":
    unittest.main()
