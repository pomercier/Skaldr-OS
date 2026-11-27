"""ArtCraft must be a locally runnable, checksum-pinned desktop application."""
import hashlib
from pathlib import Path
import os
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "scripts/skaldr-stage-artcraft.sh"
LAUNCHER = ROOT / "archiso/airootfs/usr/local/bin/skaldr-artcraft"
DESKTOP = ROOT / "archiso/airootfs/usr/share/applications/skaldr-artcraft.desktop"

VERSION = "0.19.2"
SHA256 = "0218089916d60b4d288825d1542f13cb2ca5fb691418f4102201f43a84d1be7b"


class ArtCraftReleaseTests(unittest.TestCase):
    def test_shell_entrypoints_have_valid_syntax(self):
        for path in (STAGE, LAUNCHER):
            process = subprocess.run(["bash", "-n", str(path)], capture_output=True,
                                     text=True, timeout=10, check=False)
            self.assertEqual(process.returncode, 0, process.stderr)

    def test_official_release_and_digest_pinned(self):
        stage = STAGE.read_text()
        self.assertIn(
            f"https://github.com/storytold/craft-launcher/releases/download/"
            f"v{VERSION}/artcraft-launcher-{VERSION}-linux-x86_64.AppImage",
            stage,
        )
        self.assertIn(f'checksum="{SHA256}"', stage)
        self.assertIn("sha256sum --check --status", stage)
        self.assertIn("install -m 0755", stage)
        self.assertIn(f"storytold/craft-launcher/v{VERSION}/$filename", stage)
        self.assertNotIn("0.19.0", stage)

    def test_launcher_is_local_with_diagnostics_and_fuse_fallback(self):
        launcher = LAUNCHER.read_text()
        desktop = DESKTOP.read_text()
        self.assertIn('app="/opt/skaldr/artcraft/artcraft-launcher.AppImage"', launcher)
        self.assertIn(f'expected_sha="{SHA256}"', launcher)
        self.assertIn('== "--diagnose"', launcher)
        self.assertIn("APPIMAGE_EXTRACT_AND_RUN=1", launcher)
        self.assertIn('"$app" "$@"', launcher)
        self.assertIn('exit "$result"', launcher)
        self.assertNotIn("xdg-open", launcher)
        self.assertNotIn("github.com", launcher)
        self.assertIn("Exec=/usr/local/bin/skaldr-artcraft", desktop)
        self.assertIn("Icon=applications-graphics", desktop)


    def test_real_installed_artcraft_requires_sha256_and_visible_native_gui(self):
        quicktest = (ROOT / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertIn("function test_installed_artcraft_launcher()", quicktest)
        self.assertIn("    test_installed_artcraft_launcher\n", quicktest)
        self.assertIn('"${TEST_BOOTLOADER:-}" != "grub"', quicktest)
        self.assertIn('"${TEST_FILESYSTEM:-}" != "ext4"', quicktest)
        self.assertIn("konsole --hold -e /usr/local/bin/skaldr-artcraft --diagnose", quicktest)
        # Archived GRUB/ext4 guest screenshots prove checksum success, but
        # tiny "Bundled AppImage" text is misread by OCR as "Bundled AppInag".
        # Both markers appear only after the complete SHA-256 comparison.
        self.assertIn('qt_wait_for_text "$FUNCNAME" "executable verified"', quicktest)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "GUI startup not tested"', quicktest)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Bundled AppImage"', quicktest)
        self.assertIn('qt_send_string_return "skaldr-artcraft"', quicktest)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "ARTCRAFT"', quicktest)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "2D vector animation"', quicktest)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "AniCraft"', quicktest)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "AVAILABLE TO INSTALL"', quicktest)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "PhotoCraft"', quicktest)
        self.assertIn("PASS: installed ArtCraft AppImage SHA-256 and native catalog GUI", quicktest)

    def test_visual_catalog_evidence_survives_stylized_title_ocr(self):
        # Actual archived ArtCraft screenshot_0055: "AnIiCraft" is an OCR
        # error, but the same populated installed GUI displays these
        # independent, reproducibly recognized catalog markers.
        from_text = (
            "ARTCRAFT CRAFT APP SUITE\n"
            "AnIiCraft BY ARTCRAFT\n"
            "2D vector animation\n"
            "AVAILABLE TO INSTALL\n"
            "Download size: 18 MB\n"
        )
        self.assertNotIn("AniCraft", from_text)
        for marker in ("ARTCRAFT", "2D vector animation", "AVAILABLE TO INSTALL"):
            self.assertIn(marker, from_text)
        case = (ROOT / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertIn('qt_wait_for_text "$FUNCNAME" "2D vector animation" 10 5', case)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "AVAILABLE TO INSTALL" 10 5', case)
        self.assertLess(case.index("executable verified"),
                        case.index('qt_wait_for_text "$FUNCNAME" "2D vector animation" 10 5'))

    def test_artcraft_retest_reuses_previous_iso_and_no_calamares_build(self):
        workflow = (ROOT / ".github/workflows/skaldr-artcraft-retest.yml").read_text()
        self.assertIn('run-id: 44132973459', workflow)
        self.assertIn('name: skaldr-os-x86_64-261117', workflow)
        self.assertIn("a4bb1da1b2460cf5192099e8194b61310a4539fc", workflow)
        self.assertIn("sha256sum -c SHA256SUMS", workflow)
        self.assertIn("test_install_calamares cachyos dailylive", workflow)
        self.assertIn("  actions: read", workflow)
        self.assertNotIn("buildiso.sh", workflow)
        self.assertNotIn("skaldr-build-calamares.sh", workflow)

    def test_iso_artifact_does_not_recompress_squashfs(self):
        workflow = (ROOT / ".github/workflows/build.yml").read_text()
        self.assertIn("uses: actions/upload-artifact@v4", workflow)
        self.assertIn("          path: out/desktop/*", workflow)
        self.assertIn("          compression-level: 0", workflow)

    def test_local_diagnostics_check_executable_and_digest(self):
        launcher = LAUNCHER.read_text()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake_app = root / "test-app.AppImage"
            fake_app.write_text("#!/bin/sh\nexit 0\n")
            fake_app.chmod(0o755)
            digest = hashlib.sha256(fake_app.read_bytes()).hexdigest()
            fake_script = root / "skaldr-artcraft"
            fake_script.write_text(
                launcher.replace(
                    'app="/opt/skaldr/artcraft/artcraft-launcher.AppImage"',
                    f'app="{fake_app}"',
                ).replace(f'expected_sha="{SHA256}"', f'expected_sha="{digest}"')
            )
            env = os.environ.copy()
            env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
            checked = subprocess.run(["bash", str(fake_script), "--diagnose"],
                                     env=env, capture_output=True, text=True,
                                     check=False, timeout=10)
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertIn("executable verified; GUI startup not tested", checked.stdout)
            fake_app.write_text("#!/bin/sh\nexit 9\n")
            failed = subprocess.run(["bash", str(fake_script), "--diagnose"],
                                    env=env, capture_output=True, text=True,
                                    check=False, timeout=10)
            self.assertEqual(failed.returncode, 1)
            self.assertIn("checksum mismatch", failed.stderr)


if __name__ == "__main__":
    unittest.main()
