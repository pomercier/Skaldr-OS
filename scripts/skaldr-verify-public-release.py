#!/usr/bin/env python3
"""Verify a PUBLIC Skaldr release independently against validated CI hashes.

Read-only until the local reassembly stage. Never execute scripts downloaded
from a GitHub Release. Use this repository's audited release-assets packer.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "docs/PUBLIC-PREVIEW-1-LOCK.json"
PACKER = ROOT / "scripts/skaldr-release-assets.py"
HEX_SHA = re.compile(r"^[0-9a-f]{64}$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+-preview\.[1-9][0-9]*$")
MAX_ASSET = 2 * 1024**3


class ReleaseVerificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReleaseVerificationError(message)


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def expected_assets(lock):
    names = {x["name"]: x["bytes"] for x in lock["parts"]}
    names.update({k: v["bytes"] for k, v in lock["small_assets"].items()})
    return names


def validate_lock(lock):
    require(isinstance(lock, dict), "Validation lock must be a JSON object")
    require(isinstance(lock.get("tag"), str) and TAG.fullmatch(lock["tag"]),
            "Lock contains an invalid preview tag")
    require(re.fullmatch(r"[0-9a-f]{40}", lock.get("source_sha", "")) is not None,
            "Lock source SHA must be exactly 40 lowercase hexadecimal characters")
    require(isinstance(lock.get("iso_name"), str) and
            re.fullmatch(r"skaldr-[0-9A-Za-z.+_-]+-x86_64\.iso", lock["iso_name"]),
            "Invalid locked ISO filename")
    require(isinstance(lock.get("iso_sha256"), str) and
            HEX_SHA.fullmatch(lock["iso_sha256"]), "Missing locked ISO SHA-256")
    parts = lock.get("parts")
    require(isinstance(parts, list) and 2 <= len(parts) <= 999, "Invalid part list")
    for i, item in enumerate(parts, start=1):
        require(isinstance(item, dict), "Invalid part record")
        require(item.get("name") == f'{lock["iso_name"]}.part{i:03d}',
                "Parts are not sequentially named")
        require(isinstance(item.get("sha256"), str) and
                HEX_SHA.fullmatch(item["sha256"]), "Invalid locked part SHA-256")
        require(type(item.get("bytes")) is int and 0 < item["bytes"] < MAX_ASSET,
                "Invalid locked part size")
    small = lock.get("small_assets")
    require(isinstance(small, dict) and
            set(small) == {"SHA256SUMS", "SHA256SUMS.parts",
                           "ASSEMBLE.txt", "reassemble-skaldr-iso.py"},
            "Lock must include exactly four standard helper files")
    for name, info in small.items():
        require(isinstance(info, dict), f"Invalid locked asset: {name}")
        require(isinstance(info.get("sha256"), str) and
                HEX_SHA.fullmatch(info["sha256"]), f"Invalid SHA-256: {name}")
        require(type(info.get("bytes")) is int and 0 < info["bytes"] < MAX_ASSET,
                f"Invalid size: {name}")
    require(len(expected_assets(lock)) == len(parts) + 4, "Duplicate asset names")
    return lock


def validate_release_metadata(metadata, lock):
    validate_lock(lock)
    require(isinstance(metadata, dict), "Invalid release metadata JSON")
    require(metadata.get("tag_name") == lock["tag"], "Unexpected release tag")
    require(metadata.get("target_commitish") == lock["source_sha"],
            "Release target differs from the validated source commit")
    require(metadata.get("prerelease") is True, "Expected development prerelease")
    require(metadata.get("draft") is False, "Unpublished draft release")
    require(metadata.get("published_at"), "Missing release publication timestamp")
    assets = metadata.get("assets")
    require(isinstance(assets, list), "Release asset metadata missing")
    allowed = expected_assets(lock)
    require(len(assets) == len(allowed), "Wrong number of public release assets")
    seen = set()
    for item in assets:
        require(isinstance(item, dict), "Invalid published asset metadata")
        name = item.get("name")
        require(isinstance(name, str) and name not in seen and name in allowed,
                "Unknown or duplicate published release asset")
        seen.add(name)
        require(type(item.get("size")) is int and item["size"] == allowed[name],
                f"Unexpected public asset size: {name}")
        require(item.get("state") in (None, "uploaded"),
                f"Public asset not fully uploaded: {name}")
        require(item.get("browser_download_url") ==
                f'https://github.com/pomercier/Skaldr-OS/releases/download/{lock["tag"]}/{name}',
                f"Unexpected release download destination: {name}")
    require(seen == set(allowed), "Missing expected public release assets")
    return True


def validate_downloaded_assets(directory, lock):
    validate_lock(lock)
    require(directory.is_dir() and not directory.is_symlink(),
            "Release asset directory is missing or a symlink")
    expected = expected_assets(lock)
    actual = {p.name for p in directory.iterdir()}
    require(actual == set(expected), "Downloaded release assets differ from pinned list")
    for name, length in expected.items():
        path = directory / name
        require(path.is_file() and not path.is_symlink() and path.stat().st_size == length,
                f"Downloaded public release asset missing or wrong size: {name}")
    for name, info in lock["small_assets"].items():
        require(sha256_file(directory / name) == info["sha256"],
                f"Public helper file differs from validated ISO CI artifact: {name}")
    iso_manifest = f'{lock["iso_sha256"]}  {lock["iso_name"]}\n'
    part_manifest = "".join(
        f'{item["sha256"]}  {item["name"]}\n' for item in lock["parts"])
    require((directory / "SHA256SUMS").read_text(encoding="utf-8") == iso_manifest,
            "Public ISO manifest differs from validated source")
    require((directory / "SHA256SUMS.parts").read_text(encoding="utf-8") == part_manifest,
            "Public parts manifest differs from validated source")
    return True


def verify_reassembly(directory, lock, packer=PACKER):
    # The downloaded reassembler is checked for integrity but NEVER executed.
    # The trusted checked-out repository's packer performs the reconstruction.
    completed = subprocess.run(
        [sys.executable, str(packer), "reassemble", "--directory", str(directory)],
        capture_output=True, text=True, timeout=1200, check=False,
    )
    require(completed.returncode == 0,
            f"Downloaded release did not reassemble: {completed.stderr[-1100:]}")
    iso = directory / lock["iso_name"]
    require(iso.is_file() and not iso.is_symlink(), "Verified ISO was not created")
    expected_bytes = sum(item["bytes"] for item in lock["parts"])
    require(iso.stat().st_size == expected_bytes, "Reassembled ISO size differs")
    # The trusted packer has already SHA-256-verified each part and the ISO.
    return {"tag": lock["tag"], "source_sha": lock["source_sha"],
            "iso": iso.name, "iso_sha256": lock["iso_sha256"],
            "bytes": expected_bytes, "status": "PASS"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("metadata", "verify"))
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        lock = validate_lock(json.loads(args.lock.read_text(encoding="utf-8")))
        metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
        validate_release_metadata(metadata, lock)
        if args.phase == "metadata":
            print(f"PASS: public release metadata matches validated {lock['tag']}")
            return 0
        require(args.directory is not None, "--directory required for verify phase")
        validate_downloaded_assets(args.directory, lock)
        report = verify_reassembly(args.directory, lock)
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"PASS: public {report['tag']} asset downloads and full ISO SHA-256 verified")
        return 0
    except (OSError, ValueError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: public release verification: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
