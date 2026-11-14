#!/usr/bin/env python3
"""Index actual Quicktest screenshots and OCR without suppressing test failures.

This collects evidence, not an image-comparison approval or a substitute for
the full install/reboot/login assertions in Quicktest.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


CUES = {
    "skaldr_welcome": "welcome to skaldr os",
    "installer_start": "skaldr os installer",
    "calamares_done": "all done",
    "plasma_login": "show on-screen keyboard",
    "failure_message": "installation failed",
}


def inventory(root):
    results = []
    for image in sorted(Path(root).rglob("screenshot_*.ppm")):
        # Avoid reading entire potentially large PPM into memory.
        with image.open("rb") as f:
            header = [f.readline().strip() for _ in range(3)]
        if header[0] != b"P6":
            raise ValueError(f"Unexpected PPM format: {image.name}")
        digest = hashlib.sha256()
        with image.open("rb") as source:
            for block in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(block)
        ocr = image.with_suffix(".txt")
        text = ocr.read_text(encoding="utf-8", errors="replace").lower() if ocr.is_file() else ""
        matches = [name for name, phrase in CUES.items() if phrase in text]
        # Do not attach OCR text: it could contain user-input fields.
        results.append({
            "screen": image.name,
            "stage": re.sub(r"^screenshot_\d+_", "", image.stem),
            "pixels": header[1].decode("ascii", errors="replace"),
            "sha256": digest.hexdigest(),
            "has_ocr": ocr.is_file(),
            "recognition_cues": matches,
        })
    return {
        "schema": "skaldr.visual-ci-evidence.v1",
        "image_count": len(results),
        "screenshots": results,
        "warning": "Evidence only. Manual visual review and real UI tests still required.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    index = inventory(args.results_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2) + "\n")
    print("Indexed " + str(index["image_count"]) + " actual VM screenshots")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        sys.exit(f"Skaldr visual evidence: {exc}")
