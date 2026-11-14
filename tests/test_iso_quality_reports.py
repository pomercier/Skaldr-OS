"""Build footprint and VM visual-evidence tooling tests (offline)."""
from pathlib import Path
import hashlib
import json
import runpy
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
AUDIT = runpy.run_path(str(REPO / "scripts/skaldr-iso-audit.py"), run_name="offline_test")
VISUAL = runpy.run_path(str(REPO / "scripts/skaldr-visual-evidence.py"), run_name="offline_test")


class IsoAuditTests(unittest.TestCase):
    def test_measure_actual_iso_and_do_not_invent_package_sizes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / "packages.txt"
            manifest.write_text("plasma-desktop\nsteam\ncmake\n# omitted\n")
            iso = root / "skaldr-dev.iso"
            iso.write_bytes(b"ISODATA" * 100)
            (root / "SHA256SUMS").write_text("a" * 64 + "  skaldr-dev.iso\n")
            output = AUDIT["summarize"](manifest, root)
            self.assertEqual(output["iso_size_bytes"], 700)
            self.assertEqual(output["sha256_from_build_manifest"], "a" * 64)
            self.assertEqual(output["manifest_package_count"], 3)
            self.assertIn("steam", output["package_categories"]["gaming"])
            self.assertNotIn("estimated_package_savings_bytes", output)
            self.assertEqual(output["duplicate_package_names"], [])

    def test_duplicate_packages_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "p").write_text("steam\nsteam\n")
            (root / "one.iso").write_bytes(b"valid")
            result = AUDIT["summarize"](root / "p", root)
            self.assertEqual(result["duplicate_package_names"], ["steam"])


class VisualEvidenceTests(unittest.TestCase):
    def test_screenshots_indexed_without_leaking_full_ocr(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / "screenshot_0004_test_launch_calamares.ppm"
            data = b"P6\n1 1\n255\n\xff\x00\x01"
            image.write_bytes(data)
            (root / "screenshot_0004_test_launch_calamares.txt").write_text(
                "Welcome to Skaldr OS\nprivate@example.invalid\n")
            result = VISUAL["inventory"](root)
            self.assertEqual(result["image_count"], 1)
            screen = result["screenshots"][0]
            self.assertEqual(screen["sha256"], hashlib.sha256(data).hexdigest())
            self.assertIn("skaldr_welcome", screen["recognition_cues"])
            self.assertEqual(screen["stage"], "test_launch_calamares")
            self.assertNotIn("private@example.invalid", json.dumps(result))

    def test_mp4_only_is_indexed_after_quicktest_discards_ppms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            video = root / "cachyos/dailylive/quicktest.mp4"
            video.parent.mkdir(parents=True)
            data = b"recording-byte-content-from-quicktest"
            video.write_bytes(data)
            result = VISUAL["inventory"](root)
            self.assertEqual(result["schema"], "skaldr.visual-ci-evidence.v2")
            self.assertEqual(result["video_count"], 1)
            self.assertEqual(result["screenshot_count"], 0)
            self.assertEqual(result["image_count"], 0)
            self.assertEqual(result["videos"][0]["sha256"], hashlib.sha256(data).hexdigest())
            self.assertEqual(result["videos"][0]["recording"],
                             "cachyos/dailylive/quicktest.mp4")

    def test_ci_sampling_uses_bounded_frames_and_no_full_video_text(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "quicktest.mp4").write_bytes(b"synthetic-video")
            output = root / "ci/visual-frames"
            def mocked_sample(_video, meta, folder, count):
                folder.mkdir(parents=True, exist_ok=True)
                self.assertEqual(count, 3)
                self.assertEqual(meta["duration_seconds"], 126.0)
                frames = []
                for i in range(count):
                    image = folder / f"vm-frame-{i + 1:02d}.png"
                    image.write_bytes(b"PNG-" + bytes([i]))
                    frames.append({"file": image.name,
                                   "at_seconds": float(i),
                                   "sha256": hashlib.sha256(image.read_bytes()).hexdigest()})
                return frames, None
            globals_ = VISUAL["inventory"].__globals__
            with patch.dict(globals_, {
                "video_info": lambda _p: {"duration_seconds": 126.0,
                                           "width": 1408, "height": 792},
                "sample_video": mocked_sample,
            }):
                result = VISUAL["inventory"](root, frames_dir=output,
                                              frames_per_video=3)
            self.assertEqual(result["video_count"], 1)
            self.assertEqual(result["image_count"], 3)
            self.assertEqual(len(result["videos"][0]["frames"]), 3)
            self.assertEqual(len(list(output.rglob("*.png"))), 3)
            self.assertNotIn("synthetic-video", json.dumps(result))
            with self.assertRaisesRegex(ValueError, "between 0 and 6"):
                VISUAL["inventory"](root, frames_per_video=7)

    def test_invalid_ppm_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "screenshot_0001_test.ppm").write_text("invalid image")
            with self.assertRaises(ValueError):
                VISUAL["inventory"](root)


if __name__ == "__main__":
    unittest.main()
