# Release readiness: evidence before stability

Skaldr OS **v0.1.0-preview.144** is the latest real, published, VM-tested development preview ([5/5 ISO validation](https://github.com/pomercier/Skaldr-OS/actions/runs/45245780889), [independent public reconstruction](https://github.com/pomercier/Skaldr-OS/actions/runs/45252577846)).
It is **not** certified on physical hardware. Its exact public ISO was independently
reconstructed and matched SHA-256. The [RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json) preview record now identifies the exact November 23 tested ISO, its SHA-256, and its source, VM and public-download CI evidence. The stable section deliberately remains untested and must not be interpreted as proof of physical hardware testing.

## Proven release-mode validation

The [2026-11-23 qualification workflow](https://github.com/pomercier/Skaldr-OS/actions/runs/45245780277)
successfully built the non-development `skaldr-0.1.0-x86_64.iso` and passed
its complete five-job real-VM installation and SHA-256 verification matrix.
The source revision is `bb8939175b24f4ebf30309081603bfa08d650d5d` and the candidate ISO hash is
`32f2bb6d02d90378bcd2250a24404b810ddc7239df00e28c0a48436e8d3b148b`.
This is a pre-v1 release-mode **qualification**, not a `v1.0.0` stable build;
the stable `release_mode_iso` field remains blocked pending a separately
pinned v1 release build and appropriate physical testing. Do not interpret
a green workflow as hardware certification.

## Machine-readable status

Run from the checkout with Python 3:

```sh
python3 scripts/skaldr-release-readiness.py
python3 scripts/skaldr-release-readiness.py --output release-readiness.json
python3 scripts/skaldr-release-readiness.py --require-stable-evidence
```

The final command intentionally fails while required tests have no evidence.
The readiness report validates the recorded release-candidate SHA-256, source
revision, ISO name and evidence URL as **offline metadata only**. It explicitly
marks `release_candidate_is_stable` as `false`. This is not a fresh
re-download or proof of physical hardware testing.
The [readiness workflow](../.github/workflows/skaldr-readiness.yml) publishes
the same *offline* assessment as a small GitHub Actions artifact and in its run
summary; the larger Desktop ISO build is not required. A valid link or recorded
`pass` is not independently re-tested by this script.

## Promotion gate for v1.0.0 stable

Before considering any stable tag, **perform and review** every required test:

1. Build an actual **release-mode** ISO from a distinct, pinned source commit
   and complete the full CI installation matrix; verify its published checksum.
2. Install on independent disposable physical storage with NVIDIA, AMD and
   Intel GPUs; preserve test reports showing exact builds and any failures.
3. Prove physical UEFI GRUB/ext4 and Limine/Btrfs installation, cold reboot,
   KDE login, consent-based driver choice, sound/network and desktop usability.
4. Prove offline Btrfs rollback, boot recovery, update cycles, suspend/resume
   and graphics operation. Check a fallback kernel without risky parameters.
5. Manually approve the visual baseline and review redaction and diagnostics.
6. Explicitly test Secure Boot and encrypted installations, **or** publish
   documented unsupported status with real supporting evidence.

Record each completed check in `RELEASE-EVIDENCE.json` as
`{"status":"pass","evidence_url":"https://..."}`. Missing or unsupported
mandatory categories block release readiness. The only permitted documented
exceptions are Secure Boot and encrypted installation, with evidence of
clearly disclosed unsupported behavior. Never mark hardware tested because
QEMU passed. Scrub private identifiers from public reports.

**Even when every field is filled**, the script never authorizes a release.
The existing `skaldr-release.yml` continues to block stable publication until
a separate human review changes that explicit policy. Published previews and their checksums must not be overwritten or silently replaced.

A privacy-limited `skaldr-hardware-probe` command is included in newer
development ISO sources to assist real hardware testing. It **does not** run
the required installation, graphics, suspend or rollback procedures itself,
and is absent from the previously validated preview.3 ISO.

For the hands-on procedures see [HARDWARE-TESTING.md](HARDWARE-TESTING.md).
