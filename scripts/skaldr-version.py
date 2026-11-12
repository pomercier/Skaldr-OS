#!/usr/bin/env python3
"""Generate traceable Skaldr OS build identity from first-parent project history.

This counts commits since the original CachyOS fork point, not all inherited
CachyOS history. Upstream merges count as one integration event on master.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FORK_POINT = "3215497d2e8c5fea90e185affcf973dfa2cf790b"


def git(*args):
    result = subprocess.run(
        ["git", "-c", f"safe.directory={ROOT}", "-C", str(ROOT), *args],
        capture_output=True, text=True, check=True)
    return result.stdout.strip()


def get_metadata():
    base = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", base):
        raise ValueError("VERSION must be MAJOR.MINOR.PATCH")
    sha = git("rev-parse", "HEAD")
    # Never substitute a bogus count if the required fork point is missing.
    git("merge-base", "--is-ancestor", FORK_POINT, "HEAD")
    count = int(git("rev-list", "--first-parent", "--count", f"{FORK_POINT}..HEAD"))
    short = sha[:8]
    release = os.environ.get("SKALDR_RELEASE_VERSION", "").strip().removeprefix("v")
    if release and release != base:
        raise ValueError("Release version must exactly match VERSION")
    iso_version = base if release else f"{base}-dev.{count}"
    version = iso_version if release else f"{iso_version}+g{short}"
    now = datetime.fromtimestamp(
        int(os.environ["SOURCE_DATE_EPOCH"]), timezone.utc
    ) if "SOURCE_DATE_EPOCH" in os.environ else datetime.now(timezone.utc)
    return {
        "distribution": "Skaldr OS",
        "version": version,
        "iso_version": iso_version,
        "release_line": base,
        "development": not bool(release),
        "project_commit_count": count,
        "git_revision": sha,
        "upstream_fork_point": FORK_POINT,
        "build_date_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "architecture": "x86_64",
        "source": "https://github.com/pomercier/Skaldr-OS",
    }


def install_identity(root, metadata):
    root = Path(root)
    info = root / "usr/share/skaldr/build.json"
    info.parent.mkdir(parents=True, exist_ok=True)
    info.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    release = root / "etc/skaldr-release"
    release.parent.mkdir(parents=True, exist_ok=True)
    release.write_text(
        f'SKALDR_VERSION="{metadata["version"]}"\n'
        f'SKALDR_COMMIT="{metadata["git_revision"]}"\n'
        f'SKALDR_BUILD_DATE="{metadata["build_date_utc"]}"\n',
        encoding="utf-8")
    # Preserve inherited Arch identity for package and compatibility tooling.
    source = root / "usr/share/skaldr/os-release"
    if not source.is_file():
        raise ValueError("Skaldr os-release template is missing")
    original = source.read_text(encoding="utf-8")
    original = "\n".join(line for line in original.splitlines()
                         if not line.startswith(("VERSION_ID=", "VERSION=")))
    updated = original.rstrip() + (
        f'\nVERSION="{metadata["version"]}"'
        f'\nVERSION_ID="{metadata["iso_version"]}"\n')
    source.write_text(updated, encoding="utf-8")
    (root / "etc/os-release").write_text(updated, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--field", choices=[
        "version", "iso_version", "project_commit_count", "git_revision",
        "build_date_utc", "release_line"])
    parser.add_argument("--install-to", metavar="AIROOTFS")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    metadata = get_metadata()
    if args.install_to:
        install_identity(args.install_to, metadata)
    if args.field:
        print(metadata[args.field])
    elif args.json or not args.install_to:
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
