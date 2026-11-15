#!/usr/bin/env python3
"""Read-only Btrfs partition discovery in a disposable raw GPT disk image.

Read the primary Btrfs superblock magic at filesystem offset 0x10040,
independent of udev/blkid caches or loop-device partition probing.
This does not modify the image; the Linux Btrfs mount must still validate it.
"""
import json
import os
from pathlib import Path
import stat
import sys


BTRFS_MAGIC = b"_BHRfS_M"
BTRFS_MAGIC_OFFSET = 0x10040


def select_root(raw_path, layout):
    """Return (byte_offset, byte_length) for the unique Btrfs GPT partition."""
    path = Path(raw_path)
    mode = path.lstat().st_mode
    if not stat.S_ISREG(mode) or path.is_symlink():
        raise ValueError("Refusing non-regular or symlinked raw image")
    size = path.stat().st_size
    table = layout.get("partitiontable", {})
    if table.get("label", "").lower() != "gpt":
        raise ValueError("Expected a GPT partition table")
    sectorsize = table.get("sectorsize", 512)
    if type(sectorsize) is not int or sectorsize not in (512, 4096):
        raise ValueError("Invalid GPT sector size")
    parts = table.get("partitions", [])
    if not isinstance(parts, list) or not 1 <= len(parts) <= 16:
        raise ValueError("Invalid partition count")
    matches = []
    bounds = []
    with path.open("rb") as source:
        for part in parts:
            if not isinstance(part, dict):
                raise ValueError("Invalid partition descriptor")
            start, count = part.get("start"), part.get("size")
            if type(start) is not int or type(count) is not int:
                raise ValueError("Non-integer partition geometry")
            if start <= 0 or count <= 0:
                raise ValueError("Invalid GPT partition range")
            offset, length = start * sectorsize, count * sectorsize
            if offset + length > size or length < BTRFS_MAGIC_OFFSET + len(BTRFS_MAGIC):
                # A small EFI partition is valid, but an out-of-range one is not.
                if offset + length > size:
                    raise ValueError("Partition extends beyond the raw image")
                continue
            bounds.append((offset, offset + length))
            source.seek(offset + BTRFS_MAGIC_OFFSET)
            if source.read(len(BTRFS_MAGIC)) == BTRFS_MAGIC:
                matches.append((offset, length))
    if len(matches) != 1:
        raise ValueError(
            f"Expected exactly one installed Btrfs partition (found {len(matches)} "
            "primary superblock signatures)"
        )
    return matches[0]


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: skaldr-find-btrfs-partition.py RAW_IMAGE < GPT_JSON")
    try:
        layout = json.load(sys.stdin)
        offset, length = select_root(sys.argv[1], layout)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Fail-closed GPT/Btrfs detection: {error}", file=sys.stderr)
        raise SystemExit(1) from None
    print(offset, length)


if __name__ == "__main__":
    main()
