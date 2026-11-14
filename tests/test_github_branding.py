"""Ensure GitHub's visible Skaldr logo stays scalable and theme-safe."""
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

REPO = Path(__file__).resolve().parents[1]
ASSET = REPO / "assets/skaldr-logo.svg"
README = REPO / "README.md"
SVG = "{http://www.w3.org/2000/svg}"

class GitHubBrandingTests(unittest.TestCase):
    def test_readme_uses_scalable_logo_not_128px_icon(self):
        source = README.read_text(encoding="utf-8")
        self.assertIn('src="assets/skaldr-logo.svg"', source)
        self.assertNotIn('<img src="assets/skaldr-logo.png"', source)
        self.assertIn('width="280" height="280"', source)
        self.assertTrue((REPO / "assets/skaldr-logo.png").is_file(),
                        "Keep the existing small icon for unrelated consumers")

    def test_svg_is_real_vector_art_and_theme_independent(self):
        source = ASSET.read_text(encoding="utf-8")
        root = ET.fromstring(source)
        self.assertEqual(root.tag, SVG + "svg")
        self.assertEqual(root.attrib["viewBox"], "0 0 1024 1024")
        self.assertEqual(root.attrib.get("width"), "1024")
        self.assertEqual(root.attrib.get("height"), "1024")
        self.assertTrue(root.find(SVG + "title") is not None)
        self.assertTrue(root.find(SVG + "desc") is not None)
        self.assertGreaterEqual(len(root.findall(".//" + SVG + "path")), 16)
        self.assertGreaterEqual(len(root.findall(".//" + SVG + "linearGradient")), 3)
        self.assertIn('fill="#0a1324"', source,
                      "Dark background must keep wordmark legible on GitHub light theme")
        self.assertNotIn("<script", source.lower())
        self.assertNotIn("<image", source.lower(),
                         "No embedded low-resolution raster or remote image")
        self.assertNotIn("data:image", source.lower())
        self.assertLess(len(source.encode("utf-8")), 30_000)

if __name__ == "__main__":
    unittest.main()
