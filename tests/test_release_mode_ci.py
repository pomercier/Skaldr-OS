"""The release-mode ISO must use the full VM matrix and never auto-publish."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseModeCITests(unittest.TestCase):
    def test_release_mode_is_opt_in_and_builds_with_existing_matrix(self):
        build = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", build)
        self.assertIn("release_mode:", build)
        self.assertIn('SKALDR_RELEASE_VERSION="$version"', build)
        self.assertIn("Verify test-only release-mode ISO identity", build)
        self.assertIn("metadata[\"development\"] is False", build)
        self.assertIn("Testing (${{ matrix.bootloader }} / ${{ matrix.filesystem }})", build)
        self.assertIn("Verify full-size ISO preview reconstruction", build)
        self.assertIn("'release-candidate' || 'x86_64'", build)

    def test_candidate_rechecks_every_iso_relevant_source_change(self):
        build = (ROOT / ".github/workflows/build.yml").read_text(encoding="utf-8")
        candidate = (ROOT / ".github/workflows/skaldr-release-candidate.yml").read_text(encoding="utf-8")
        build_push = build.split("  push:", 1)[1].split("  pull_request:", 1)[0]
        candidate_push = candidate.split("  push:", 1)[1].split("  workflow_dispatch:", 1)[0]
        pattern = r"^      - '([^']+)'$"
        build_paths = set(re.findall(pattern, build_push, re.MULTILINE))
        candidate_paths = set(re.findall(pattern, candidate_push, re.MULTILINE))
        self.assertTrue(build_paths.issubset(candidate_paths))
        self.assertIn("archiso/**", candidate_paths)
        self.assertIn("VERSION", candidate_paths)
        self.assertIn("testcases/cachyos/dailylive/test_live_bios", candidate_paths)
        self.assertIn(".github/workflows/skaldr-release-candidate.yml", candidate_paths)
        self.assertNotIn("README.md", candidate_paths)
        self.assertNotIn("docs/**", candidate_paths)

    def test_release_candidate_isolation(self):
        workflow = (ROOT / ".github/workflows/skaldr-release-candidate.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [master]", workflow)
        self.assertIn("uses: ./.github/workflows/build.yml", workflow)
        self.assertIn("release_mode: true", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("gh release create", workflow)

    def test_public_preview_refuses_release_mode(self):
        workflow = (ROOT / ".github/workflows/skaldr-auto-verified-preview.yml").read_text(encoding="utf-8")
        self.assertIn('inputs.get("release_mode"', workflow)
        self.assertIn("Refuse release-mode", workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", workflow)

    def test_stable_release_still_fails_closed(self):
        workflow = (ROOT / ".github/workflows/skaldr-release.yml").read_text(encoding="utf-8")
        self.assertIn("Stable publishing requires a release-mode ISO and physical testing", workflow)


if __name__ == "__main__":
    unittest.main()
