# Release readiness: evidence before stability

Skaldr OS **v0.1.0-preview.151** is the latest real, published, VM-tested development preview ([6/6 ISO validation](https://github.com/pomercier/Skaldr-OS/actions/runs/45462762559), [independent public reconstruction](https://github.com/pomercier/Skaldr-OS/actions/runs/45469323148)).
It is **not** certified on physical hardware. Its exact public ISO was independently
reconstructed and matched SHA-256. The [RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json) preview record now identifies the exact November 24 tested ISO, its SHA-256, and its source, VM and public-download CI evidence. The stable section deliberately remains untested and must not be interpreted as proof of physical hardware testing.

## Proven release-mode validation

The [latest exact-source release-mode qualification](https://github.com/pomercier/Skaldr-OS/actions/runs/45462762588)
passed **six out of six VM jobs** on commit `88521c22c9e1d9cf5e4d5c79fb09413eca8f85a7`.
The non-development ISO `skaldr-0.1.0-x86_64.iso` has verified
SHA-256 `da2138bee1693b82e1656c2fffb8eb8811f45ae1498f1d4e05898c830b675d64`, recorded in the workflow's `SHA256SUMS`
manifest. This validates VM-based Calamares installation, cold boot, KDE,
legacy BIOS and Btrfs recovery, but does **not** establish real-hardware
compatibility or authorize stable `v1.0.0`. The stable `release_mode_iso`
field deliberately remains untested pending a separately pinned v1 image
and independent physical hardware evidence.

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
