# Release readiness: evidence before stability

Skaldr OS **v0.1.0-preview.148** is the latest real, published, VM-tested development preview ([6/6 ISO validation](https://github.com/pomercier/Skaldr-OS/actions/runs/45333165571), [independent public reconstruction](https://github.com/pomercier/Skaldr-OS/actions/runs/45342872881)).
It is **not** certified on physical hardware. Its exact public ISO was independently
reconstructed and matched SHA-256. The [RELEASE-EVIDENCE.json](RELEASE-EVIDENCE.json) preview record now identifies the exact November 24 tested ISO, its SHA-256, and its source, VM and public-download CI evidence. The stable section deliberately remains untested and must not be interpreted as proof of physical hardware testing.

## Proven release-mode validation

Both the [development ISO](https://github.com/pomercier/Skaldr-OS/actions/runs/45263079702) and the
[release-mode ISO](https://github.com/pomercier/Skaldr-OS/actions/runs/45263079443)
passed **6/6 real VM jobs** on [source `38c3b85`](https://github.com/pomercier/Skaldr-OS/commit/38c3b8560b43aa2e450d9cb9f16ff1d908a57685):
UEFI GRUB/ext4, UEFI Limine/Btrfs, legacy BIOS GRUB/ext4 installed cold boot
without installer ISO or OVMF, BIOS live boot and full-size SHA-256 reassembly.
The Limine/Btrfs installation additionally passed an offline root rollback
followed by KDE login. These results do not certify physical hardware.

The non-development candidate `skaldr-0.1.0-x86_64.iso` has exact
source `38c3b8560b43aa2e450d9cb9f16ff1d908a57685` and verified SHA-256 `73c72d946241760cb7ba408d0684df8e103cb2fe5b7a48f1768a7f27c841f8f4`.
Its successful virtual-machine qualification is recorded separately in
`RELEASE-EVIDENCE.json`; the stable v1.0.0 `release_mode_iso` field
intentionally remains untested until a distinct version-1 release candidate
and the required real-hardware evidence are available.

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
