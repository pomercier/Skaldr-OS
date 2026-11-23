#!/usr/bin/env python3
"""Offline, fail-closed record of release readiness.

This audits *recorded evidence*, NOT live GitHub Actions or physical hardware.
A green source check is never equivalent to a physical compatibility test.
"""
import argparse
import json
import re
import sys
from pathlib import Path

REQUIRED = (
    "release_mode_iso",
    "nvidia_physical", "amd_physical", "intel_physical",
    "uefi_grub_ext4", "uefi_limine_btrfs",
    "physical_rollback", "kernel_recovery", "update_cycles",
    "graphics_suspend", "visual_review", "privacy_review",
)
OPTIONAL_DOCUMENTED = ("secure_boot", "encrypted_install")
PROOF = re.compile(r"^https://[^\s]+$")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA64 = re.compile(r"^[0-9a-f]{64}$")
RELEASE_CANDIDATE_ISO = re.compile(r"^skaldr-[0-9]+\\.[0-9]+\\.[0-9]+-x86_64\\.iso$")
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+-preview\.[1-9][0-9]*$")


def evaluate(record):
    """Return a machine-readable audit, never an assertion of live testing."""
    errors = []
    preview = record.get("preview", {})
    if record.get("schema") != "skaldr.release-evidence.v1" or not isinstance(preview, dict):
        errors.append("Invalid release-evidence schema or preview object")
        preview = {}
    for key, pattern in (("tag", TAG), ("source_sha", SHA40), ("iso_sha256", SHA64)):
        if not pattern.fullmatch(str(preview.get(key, ""))):
            errors.append("Invalid preview " + key)
    links = preview.get("evidence", {})
    if not isinstance(links, dict):
        links = {}
    for key in ("source_tests", "iso_matrix", "public_reassembly"):
        value = links.get(key, "")
        if not isinstance(value, str) or not PROOF.fullmatch(value):
            errors.append("Missing or invalid preview evidence URL: " + key)

    # The release-mode candidate is a traceability record, not proof of
    # production readiness. Validate its metadata without promoting it.
    candidate = record.get("release_candidate")
    candidate_errors = []
    if candidate is not None:
        if not isinstance(candidate, dict):
            candidate_errors.append("Release candidate must be an object")
        else:
            if candidate.get("status") != "vm_validated_not_hardware_certified":
                candidate_errors.append("Release candidate must declare its limited VM scope")
            for key, pattern in (
                ("source_sha", SHA40),
                ("iso_sha256", SHA64),
                ("image", RELEASE_CANDIDATE_ISO),
                ("ci_evidence", PROOF),
            ):
                value = candidate.get(key)
                if not isinstance(value, str) or not pattern.fullmatch(value):
                    candidate_errors.append("Invalid release candidate " + key)
            if candidate.get("iso_sha256") == preview.get("iso_sha256"):
                candidate_errors.append("Release candidate must not reuse development ISO checksum")

    stable = record.get("stable", {})
    if not isinstance(stable, dict):
        stable = {}
    blockers = []
    for key in REQUIRED + OPTIONAL_DOCUMENTED:
        item = stable.get(key, {})
        if not isinstance(item, dict):
            item = {}
        status = item.get("status", "untested")
        proof = item.get("evidence_url", "")
        allowed = ("pass", "documented_unsupported") if key in OPTIONAL_DOCUMENTED else ("pass",)
        if status not in allowed or not isinstance(proof, str) or not PROOF.fullmatch(proof):
            blockers.append(key)
    release_sha = stable.get("release_source_sha", "")
    if not SHA40.fullmatch(str(release_sha)) or release_sha == preview.get("source_sha"):
        blockers.append("release_source_sha (separate release-mode build required)")

    return {
        "schema": "skaldr.readiness-report.v1",
        "preview_tag": preview.get("tag", ""),
        "recorded_preview_evidence_valid": not errors,
        "recorded_release_candidate_metadata_valid": candidate is not None and not candidate_errors,
        "release_candidate_metadata_errors": candidate_errors,
        "release_candidate_is_stable": False,
        "preview_metadata_errors": errors,
        "stable_evidence_complete": not errors and not candidate_errors and not blockers,
        "stable_blockers": blockers,
        "stable_publication_automatically_authorized": False,
        "disclaimer": (
            "This is an OFFLINE audit of repository-maintained evidence links and "
            "statuses, not a fresh verification of those URLs, physical tests, "
            "or approval to publish a stable release."
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence", type=Path,
                        default=Path("docs/RELEASE-EVIDENCE.json"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--require-stable-evidence", action="store_true")
    args = parser.parse_args(argv)
    result = evaluate(json.loads(args.evidence.read_text(encoding="utf-8")))
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    if result["preview_metadata_errors"] or result["release_candidate_metadata_errors"] or (
        args.require_stable_evidence and not result["stable_evidence_complete"]
    ):
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, TypeError) as exc:
        sys.exit("Release readiness audit failed closed: " + str(exc))
