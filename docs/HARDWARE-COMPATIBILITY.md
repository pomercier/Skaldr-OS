# Skaldr OS — community hardware reports

Skaldr OS is a personal fork, and compatibility is not established until a
configuration has completed real, repeatable tests. This page is a
**submission template, not a certified-device list**.

For early development, contributors can submit updates as **pull requests**
adding a test report under `docs/hardware-reports/` (GitHub Issues are
currently disabled). Avoid serial numbers, account names, MAC addresses,
IP addresses, registration keys and complete unredacted installation logs.

## Test report template

```text
Skaldr commit/tag:
ISO SHA-256:
Test date:
CPU family/model:
GPU family/model:
RAM capacity:
UEFI or legacy BIOS:
Bootloader and root filesystem:
Storage interface (no serial):
KDE / Wayland / X11:
Tested live desktop: pass / fail / untested
Cold installed boot: pass / fail / untested
Login / NumLock: pass / fail / untested
Wi-Fi / ethernet / audio: pass / fail / untested
Vulkan / video decoding: pass / fail / untested
HDR / VRR / monitor modes: pass / fail / untested
Sleep / resume: pass / fail / untested
Snapper creation / restore: pass / fail / untested
LTS boot entry: pass / fail / untested
Performance mode: pass / fail / untested
Reproduction steps and sanitized logs:
```

The optional `skaldr-gpu-diagnostics` tool can help list GPU models, Vulkan
device names, compiled FFmpeg backends and connected display counts without
changing drivers. FFmpeg's backend list is **not proof** of successful
hardware acceleration. Use `skaldr-recovery` for a read-only inventory
of kernel filenames, bootloader config presence and Snapper availability:
none of these checks claims a successful rollback.

Only independent physical-machine validation should turn an "untested" into
"pass". Keep failures visible and retain the release's exact Git SHA.
