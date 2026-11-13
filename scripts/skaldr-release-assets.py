#!/usr/bin/env python3
"""Split verified Skaldr ISO images for GitHub Releases and reassemble them.

GitHub Releases allow many assets, but each individual asset must be under
2 GiB. The release preserves the ISO's original SHA256SUMS and supplies
per-part SHA256SUMS.parts. Reassembly does not require third-party packages.
"""

import argparse
import hashlib
from pathlib import Path
import re
import shutil
import sys
import tempfile

PART_BYTES = 1900 * 1024 * 1024  # 1.86 GiB, strictly below GitHub's 2 GiB cap
MAX_ASSET_BYTES = 2 * 1024 * 1024 * 1024
COPY_BYTES = 4 * 1024 * 1024
ISO_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\.iso\Z")
CHECKSUM_LINE = re.compile(r"([0-9a-fA-F]{64}) [ *]([^\r\n]+)\Z")


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(COPY_BYTES), b""):
            digest.update(block)
    return digest.hexdigest()


def manifest_entries(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines:
        raise ValueError(f"Empty checksum manifest: {path}")
    entries = []
    for line in lines:
        match = CHECKSUM_LINE.fullmatch(line)
        if not match:
            raise ValueError(f"Malformed SHA256 checksum in {path}: {line!r}")
        checksum, filename = match.groups()
        if not filename or Path(filename).name != filename or filename in (".", ".."):
            raise ValueError(f"Unsafe checksum filename: {filename!r}")
        entries.append((filename, checksum.lower()))
    if len({name for name, _ in entries}) != len(entries):
        raise ValueError(f"Duplicate checksum filename in {path}")
    return entries


def original_iso(directory):
    entries = manifest_entries(directory / "SHA256SUMS")
    if len(entries) != 1 or not ISO_NAME.fullmatch(entries[0][0]):
        raise ValueError("SHA256SUMS must identify exactly one safe ISO filename")
    return entries[0]


def prepare(iso, checksum_file, output, part_size=PART_BYTES):
    if not (0 < part_size < MAX_ASSET_BYTES):
        raise ValueError("Part size must be greater than zero and smaller than 2 GiB")
    if not iso.is_file() or not ISO_NAME.fullmatch(iso.name):
        raise ValueError("Input ISO must exist and have a safe .iso filename")
    expected = manifest_entries(checksum_file)
    if expected != [(iso.name, digest_file(iso))]:
        raise ValueError("Source ISO does not match its original SHA256SUMS")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Release asset output directory must be empty")
    parts = []
    with iso.open("rb") as source:
        while True:
            first = source.read(min(COPY_BYTES, part_size))
            if not first:
                break
            part_name = f"{iso.name}.part{len(parts) + 1:03d}"
            if len(parts) >= 999:
                raise ValueError("Too many ISO parts")
            part_file = output / part_name
            digest = hashlib.sha256()
            written = 0
            with part_file.open("wb") as target:
                target.write(first)
                digest.update(first)
                written += len(first)
                while written < part_size:
                    block = source.read(min(COPY_BYTES, part_size - written))
                    if not block:
                        break
                    target.write(block)
                    digest.update(block)
                    written += len(block)
            parts.append((part_name, digest.hexdigest()))
    if len(parts) < 2:
        raise ValueError("ISO is too small to require splitting; expected at least two parts")
    shutil.copyfile(checksum_file, output / "SHA256SUMS")
    (output / "SHA256SUMS.parts").write_text(
        "".join(f"{hash_value}  {name}\n" for name, hash_value in parts),
        encoding="utf-8",
    )
    shutil.copyfile(Path(__file__), output / "reassemble-skaldr-iso.py")
    (output / "ASSEMBLE.txt").write_text(
        "Skaldr OS release ISO, split for GitHub's per-file size limit.\n\n"
        "Download EVERY .iso.partNNN file, SHA256SUMS, SHA256SUMS.parts,\n"
        "and reassemble-skaldr-iso.py into the SAME directory.\n\n"
        "Run (Linux/macOS with Python 3):\n"
        "  python3 reassemble-skaldr-iso.py reassemble --directory .\n"
        "Run on Windows with Python 3: use py instead of python3.\n\n"
        "The tool checks each part's SHA-256, reconstructs the original ISO,\n"
        "and checks its original SHA-256 before making it available.\n"
        "Do not flash individual .part files; flash only the verified .iso.\n",
        encoding="utf-8",
    )
    return parts


def reassemble(directory):
    iso_name, expected_iso_hash = original_iso(directory)
    entries = manifest_entries(directory / "SHA256SUMS.parts")
    expected_parts = [f"{iso_name}.part{i:03d}" for i in range(1, len(entries) + 1)]
    if len(entries) < 2 or len(entries) > 999 or [name for name, _ in entries] != expected_parts:
        raise ValueError("Non-sequential, incomplete, or unexpected ISO part manifest")
    disk_parts = sorted(p.name for p in directory.glob(f"{iso_name}.part*"))
    if disk_parts != expected_parts:
        raise ValueError("Missing or unexpected ISO part files")
    for filename, expected_hash in entries:
        part_file = directory / filename
        if not part_file.is_file() or part_file.is_symlink():
            raise ValueError(f"Missing or unsafe ISO part: {filename}")
        if part_file.stat().st_size >= MAX_ASSET_BYTES:
            raise ValueError(f"ISO part exceeds GitHub release limit: {filename}")
        if digest_file(part_file) != expected_hash:
            raise ValueError(f"SHA-256 mismatch for ISO part: {filename}")
    iso = directory / iso_name
    if iso.exists():
        if iso.is_file() and not iso.is_symlink() and digest_file(iso) == expected_iso_hash:
            return iso
        raise ValueError(f"Refusing to overwrite existing file: {iso}")
    with tempfile.NamedTemporaryFile(mode="wb", dir=directory, prefix=".skaldr-assembly-", delete=False) as target:
        temporary = Path(target.name)
        hash_total = hashlib.sha256()
        try:
            for filename, _ in entries:
                with (directory / filename).open("rb") as source:
                    for block in iter(lambda: source.read(COPY_BYTES), b""):
                        target.write(block)
                        hash_total.update(block)
            target.flush()
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    if hash_total.hexdigest() != expected_iso_hash:
        temporary.unlink(missing_ok=True)
        raise ValueError("Reassembled ISO SHA-256 does not match the original SHA256SUMS")
    temporary.replace(iso)
    return iso


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pack = sub.add_parser("prepare", help="verify and split the ISO for GitHub Releases")
    pack.add_argument("--iso", required=True, type=Path)
    pack.add_argument("--checksum", required=True, type=Path)
    pack.add_argument("--out", required=True, type=Path)
    pack.add_argument("--part-size", type=int, default=PART_BYTES, help=argparse.SUPPRESS)
    join = sub.add_parser("reassemble", help="verify and reconstruct the full ISO")
    join.add_argument("--directory", type=Path, default=Path("."))
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            parts = prepare(args.iso, args.checksum, args.out, args.part_size)
            print(f"Verified and prepared {len(parts)} ISO parts in {args.out}")
        else:
            result = reassemble(args.directory)
            print(f"Verified and reconstructed ISO: {result}")
    except (ValueError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
