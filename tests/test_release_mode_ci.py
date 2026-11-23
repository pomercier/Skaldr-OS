"""The release-mode ISO must use the full VM matrix and never auto-publish."""
from pathlib import Path
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
