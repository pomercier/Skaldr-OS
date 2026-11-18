# Release readiness: evidence before stability

Skaldr OS **v0.1.0-preview.3** is a real, published, VM-tested development preview.
It is **not** certified on physical hardware. Its exact public ISO was independently
reconstructed and matched SHA-256. The three links to those CI runs are pinned in
[RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json).

## Machine-readable status

Run from the checkout with Python 3:

```sh
python3 scripts/skaldr-release-readiness.py
python3 scripts/skaldr-release-readiness.py --output release-readiness.json
python3 scripts/skaldr-release-readiness.py --require-stable-evidence
```

The final command intentionally fails while required tests have no evidence.
The [readiness workflow](../.github/workflows/skaldr-readiness.yml) publishes
the same *offline* assessment as a small GitHub Actions artifact and in its run
summary; the larger Desktop ISO build is not required. A valid link or recorded
`pass` is not independently re-tested by this script.

## Promotion gate for v0.1.0 stable

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
a separate human review changes that explicit policy. Preview.3 and its hashes
must not be overwritten or silently replaced.

For the hands-on procedures see [HARDWARE-TESTING.md](HARDWARE-TESTING.md).
