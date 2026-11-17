"""A one-time request may only dispatch the exact SHA-pinned preview.2."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REQUEST = ROOT / 'docs/PREVIEW2-PUBLISH-REQUEST.json'
WORKFLOW = ROOT / '.github/workflows/skaldr-preview2-one-shot-dispatch.yml'
LOCK = ROOT / 'docs/PUBLIC-PREVIEW-2-LOCK.json'

class OneShotPreviewDispatchTests(unittest.TestCase):
    def test_request_matches_cryptographically_locked_candidate(self):
        lock = json.loads(LOCK.read_text())
        request = json.loads(REQUEST.read_text())
        self.assertEqual(request, {
            'tag': 'v0.1.0-preview.2',
            'source_sha': lock['source_sha'],
            'validated_iso_run_id': lock['validated_iso_run_id'],
            'source_checks_run_id': lock['source_checks_run_id'],
            'iso_sha256': lock['iso_sha256'],
        })

    def test_dispatch_is_one_shot_and_retains_independent_release_gate(self):
        script = WORKFLOW.read_text()
        self.assertIn('on:\n  push:\n    branches: [master]', script)
        self.assertIn("      - 'docs/PREVIEW2-PUBLISH-REQUEST.json'", script)
        self.assertIn('  actions: write', script)
        self.assertIn('  contents: read', script)
        self.assertIn('HEAD^:docs/PREVIEW2-PUBLISH-REQUEST.json', script)
        self.assertIn('if request != required:', script)
        self.assertIn('test "$iso_result" = success', script)
        self.assertIn('test "$source_result" = success', script)
        self.assertIn('select(.expired == false)', script)
        self.assertIn('gh workflow run skaldr-release.yml', script)
        self.assertIn('-f stable=false', script)
        self.assertNotIn('gh release create', script)
        self.assertNotIn('gh release upload', script)
        self.assertNotIn('force: true', script)

if __name__ == "__main__":
    unittest.main()
