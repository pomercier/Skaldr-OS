# Independent verification of the published Skaldr preview

A GitHub Release can appear complete while its public files are missing,
truncated, tampered with, or impossible to reconstruct on another machine.
Skaldr verifies these questions separately from the original ISO builder.

## Source of truth

The pinned baseline
[`PUBLIC-PREVIEW-1-LOCK.json`](PUBLIC-PREVIEW-1-LOCK.json) records:

- The original validated source commit `b391fc35f4eaade3c1ff5231c33c10f63770bda6`.
- The independently successful five-job Desktop ISO run
  [43507233020](https://github.com/pomercier/Skaldr-OS/actions/runs/43507233020).
- The original ISO's SHA-256, all three original ISO part SHA-256 values,
  and exact part sizes.
- The SHA-256 and size of all four small helper files recovered from the
  original **CI-generated verification artifact**. These checksums are
  pinned independently of the subsequent public GitHub Release.

The [published preview.1](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.1)
exposes seven assets. This check must never trust that release's own checksum
files alone: their exact bytes must match the original validated CI artifacts.

## Independent validation workflow

The read-only
[`skaldr-public-release-verification.yml`](../.github/workflows/skaldr-public-release-verification.yml)
workflow runs on an independent Ubuntu runner. It:

1. Retrieves GitHub's published release metadata and checks the exact tag,
   pinned original commit SHA, prerelease status and all seven asset names,
   URLs and file sizes.
2. Downloads **all seven public assets** — not the original Actions ISO artifact.
3. Checks every helper file against its independently pinned SHA-256.
4. Checks both published manifests **byte-for-byte** against the original CI
   ISO and split-part checksums.
5. Executes only the vetted reassembler from the **checked-out GitHub source
   tree**; it does not execute the script downloaded from the public release.
6. Reassembles the complete multi-gigabyte ISO, checks the SHA-256 of each
   part and of the resulting ISO, and emits a small JSON result.
7. Discards the temporary download and reconstructed ISO when the CI runner
   is destroyed. The workflow does not create tags, releases, or new branches.

This test uses approximately 8.3 GB for the downloaded parts and the
reconstructed ISO combined; it is a dedicated opt-in/push-on-change workflow,
not a recurring monitor. It can fail because of a transient network problem,
in which case logs distinguish a download failure from a hash mismatch.

**Result — PASS:** The independent Ubuntu runner downloaded all seven
public v0.1.0-preview.1 files and successfully reconstructed the full
4,144,332,800-byte ISO on November 15, 2026
([GitHub Actions run 43780766882](https://github.com/pomercier/Skaldr-OS/actions/runs/43780766882)).
The reconstructed image exactly matched the originally validated SHA-256:

```text
b553c0e4cfe01e1de0c857f1dc4c70ac89d41a762bdb01750c770bb77069ec49
```

The workflow's [compact JSON report](https://github.com/pomercier/Skaldr-OS/actions/runs/43780766882)
is archived as `skaldr-public-preview1-independent-verification`.
No release, tag, or source branch was created by the verification.

A verified download says the public files reconstruct correctly and match
the original source-validated ISO. It does not certify real-world GPU,
Suspend/Resume, encrypted disks, Secure Boot, or physical hardware.

Preview.2 is now **publicly released and independently verified**:
[download v0.1.0-preview.2](https://github.com/pomercier/Skaldr-OS/releases/tag/v0.1.0-preview.2).
The [separate pinned lock](PUBLIC-PREVIEW-2-LOCK.json) preserves the source
SHA `e37fdd25e01e9564223f426c3ff4000dbdd5ef5b`, original ISO SHA-256,
three ISO part hashes and four helper-file hashes from the
[fully successful five-job ISO build](https://github.com/pomercier/Skaldr-OS/actions/runs/43924758899).

The [release workflow, second attempt](https://github.com/pomercier/Skaldr-OS/actions/runs/43996058008)
published seven public assets with exact matching SHA-256 digests and
successfully ran a **second, separate Ubuntu job** that downloaded all seven
published files from GitHub Releases and reconstructed the original ISO.
The verifier reported **PASS**, with full SHA-256:

```text
177b5667b29338db66473ebefb739551ee35edb116cd6b650e2ec6d9f4517b2e
```

The compact verification report is preserved as the workflow artifact
`skaldr-published-preview2-integrity`.
No physical compatibility is certified by these checksum and VM checks.
