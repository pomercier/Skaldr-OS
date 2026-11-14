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
import shutil
import subprocess
import sys


CUES = {
    "skaldr_welcome": "welcome to skaldr os",
    "installer_start": "skaldr os installer",
    "calamares_done": "all done",
    "plasma_login": "show on-screen keyboard",
    "failure_message": "installation failed",
}


def hash_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def video_info(video):
    if not shutil.which("ffprobe"):
        return None
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=width,height", "-of", "json", str(video)],
        capture_output=True, text=True, timeout=15, check=False,
    )
    if proc.returncode:
        return None
    try:
        record = json.loads(proc.stdout)
        duration = float(record.get("format", {}).get("duration", 0))
        streams = [x for x in record.get("streams", [])
                   if x.get("width") and x.get("height")]
        if not 0 < duration < 86400:
            return None
        return {"duration_seconds": round(duration, 2),
                "width": int(streams[0]["width"]) if streams else 0,
                "height": int(streams[0]["height"]) if streams else 0}
    except (ValueError, TypeError, KeyError):
        return None


def sample_video(video, metadata, output_dir, count):
    if metadata is None or not shutil.which("ffmpeg"):
        return [], "ffmpeg/ffprobe unavailable or duration unknown"
    output_dir.mkdir(parents=True, exist_ok=True)
    samples = []
    for i in range(count):
        seconds = round(metadata["duration_seconds"] * (i + 0.5) / count, 3)
        target = output_dir / f"vm-frame-{i + 1:02d}.png"
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss",
             str(seconds), "-i", str(video), "-vf", "scale=960:-2",
             "-frames:v", "1", "-y", str(target)],
            capture_output=True, text=True, timeout=45, check=False,
        )
        if proc.returncode or not target.exists() or not target.stat().st_size:
            target.unlink(missing_ok=True)
            return samples, "Video frame extraction failed; recording retained"
        samples.append({"file": target.name, "at_seconds": seconds,
                        "sha256": hash_file(target)})
    return samples, None


def inventory(root, frames_dir=None, frames_per_video=0):
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
    if not 0 <= frames_per_video <= 6:
        raise ValueError("frames_per_video must be between 0 and 6")
    video_results = []
    frame_count = 0
    for index, video in enumerate(sorted(Path(root).rglob("quicktest.mp4")), 1):
        metadata = video_info(video)
        item = {"recording": video.relative_to(root).as_posix(),
                "sha256": hash_file(video),
                "size_bytes": video.stat().st_size,
                "metadata": metadata, "frames": []}
        if frames_per_video:
            if frames_dir is None:
                raise ValueError("frames_dir required when sampling video")
            images, warning = sample_video(
                video, metadata, Path(frames_dir) / f"recording-{index:02d}",
                frames_per_video)
            item["frames"] = images
            frame_count += len(images)
            if warning:
                item["sampling_warning"] = warning
        video_results.append(item)
    return {
        "schema": "skaldr.visual-ci-evidence.v2",
        "screenshot_count": len(results),
        "video_count": len(video_results),
        "image_count": len(results) + frame_count,
        "screenshots": results,
        "videos": video_results,
        "warning": ("Evidence only. Sample frames can contain UI text: review before "
                    "sharing. Manual visual review and VM assertions remain required."),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames-per-video", type=int, default=3,
                        help="Extract 0 to 6 representative images from each Quicktest MP4")
    args = parser.parse_args(argv)
    if not 0 <= args.frames_per_video <= 6:
        parser.error("--frames-per-video must be 0..6")
    index = inventory(args.results_dir,
                      frames_dir=args.output.parent / "visual-frames",
                      frames_per_video=args.frames_per_video)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(index, indent=2) + "\n")
    print(f"Indexed {index['video_count']} Quicktest videos "
          f"and {index['image_count']} visual images")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        sys.exit(f"Skaldr visual evidence: {exc}")
