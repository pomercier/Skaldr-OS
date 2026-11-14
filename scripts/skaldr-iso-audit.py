#!/usr/bin/env python3
"""Summarize the *actual* compiled ISO sizes and package manifest.

A package's compressed SquashFS contribution is not inferable from the
uncompressed manifest: no imaginary per-package space savings are reported.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys


GROUPS = {
    "gaming": {"steam", "gamescope", "gamemode", "mangohud", "wine",
               "winetricks", "steam-devices"},
    "virtualization": {"qemu-desktop", "virt-manager", "libvirt",
                       "edk2-ovmf", "virtualbox-guest-utils", "open-vm-tools"},
    "development": {"gcc", "cmake", "make", "ninja", "fakeroot", "git",
                    "rust", "python", "python-pip", "uv", "yay"},
    "kde": {"plasma-desktop", "plasma-workspace", "plasma-login-manager",
            "dolphin", "konsole", "kate", "kcalc", "spectacle"},
    "multimedia": {"vlc", "audacity", "ffmpeg", "pipewire",
                   "libreoffice-fresh", "brave-bin"},
}


def summarize(manifest, iso_directory):
    packages = [line.strip() for line in Path(manifest).read_text().splitlines()
                if line.strip() and not line.lstrip().startswith("#")]
    duplicates = sorted([name for name, n in Counter(packages).items() if n > 1])
    images = sorted(Path(iso_directory).glob("*.iso"))
    if len(images) != 1:
        raise ValueError(f"Expected exactly one ISO, found {len(images)}")
    iso = images[0]
    if not iso.stat().st_size:
        raise ValueError("ISO file is empty")
    checksums = Path(iso_directory) / "SHA256SUMS"
    sha256 = None
    if checksums.exists():
        for line in checksums.read_text().splitlines():
            bits = line.split()
            if len(bits) >= 2 and bits[-1].lstrip("*") == iso.name:
                sha256 = bits[0]
    groups = {name: sorted(GROUPS[name].intersection(packages))
              for name in GROUPS}
    return {
        "schema": "skaldr.iso-footprint.v1",
        "iso_file": iso.name,
        "iso_size_bytes": iso.stat().st_size,
        "iso_size_mib": round(iso.stat().st_size / (1024 * 1024), 2),
        "sha256_from_build_manifest": sha256,
        "manifest_package_count": len(packages),
        "duplicate_package_names": duplicates,
        "package_categories": groups,
        "note": ("Size is measured on the completed ISO. Package categories "
                 "are descriptive, NOT estimates of compressible savings."),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--iso-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    data = summarize(args.manifest, args.iso_dir)
    if data["duplicate_package_names"]:
        raise ValueError("Duplicate package names: " + ", ".join(data["duplicate_package_names"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Measured ISO size: {data['iso_size_mib']} MiB "
          f"({data['manifest_package_count']} manifest entries)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        sys.exit(f"ISO footprint audit: {exc}")
