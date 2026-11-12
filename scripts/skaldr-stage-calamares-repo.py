#!/usr/bin/env python3
"""Add a temporary local package repo to a staged ArchISO pacman.conf only."""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    raise SystemExit("Usage: skaldr-stage-calamares-repo.py PACMAN_CONF ABSOLUTE_REPO")
config = Path(sys.argv[1])
repository = Path(sys.argv[2])
if not repository.is_absolute() or not (repository / "skaldr-local.db.tar.gz").is_file():
    raise SystemExit("An absolute local package repository is required")
source = config.read_text(encoding="utf-8")
marker = "[cachyos]\n"
if marker not in source or "[skaldr-local]" in source:
    raise SystemExit("Staged pacman configuration is missing its insertion point")
stanza = (
    "[skaldr-local]\n"
    "SigLevel = Optional TrustAll\n"
    f"Server = file://{repository}\n\n"
)
# Temporary build-only repo: neither /etc/pacman.conf nor the Git source changes.
config.write_text(source.replace(marker, stanza + marker, 1), encoding="utf-8")
print("Registered CI-local Calamares rebuild in staging-only pacman config")
