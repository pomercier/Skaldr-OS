#!/usr/bin/env python3
"""Static and isolated integration checks for the Skaldr OS ISO sources."""
import hashlib
import os
import runpy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "archiso" / "airootfs"
PROFILE = LIVE / "usr/local/bin/skaldr-profile"
INJECT = LIVE / "usr/local/bin/skaldr-cal-inject"
MANIFEST = LIVE / "usr/share/skaldr/packages.txt"
BOOT = [
    REPO / "archiso/grub/grub.cfg",
    REPO / "archiso/grub/loopback.cfg",
    REPO / "archiso/syslinux/archiso_sys-linux.cfg",
    REPO / "archiso/efiboot/loader/entries/01-archiso-linux.conf",
    REPO / "archiso/efiboot/loader/entries/02-archiso-linux-cachyos.conf",
]
try:
    import yaml
except ImportError:
    yaml = None

class SkaldrChecks(unittest.TestCase):
    def test_packages(self):
        live = (REPO / "archiso/packages_desktop.x86_64").read_text().splitlines()
        installed = [line.strip() for line in MANIFEST.read_text().splitlines() if line.strip()]
        self.assertEqual(len(live), len(set(live)), "Duplicate live packages")
        for package in installed:
            self.assertIn(package, live, "Target-only package: " + package)
        for package in ("brave-bin", "libreoffice-fresh", "libreoffice-fresh-fr",
                        "cmake", "make", "fakeroot", "yay", "kcalc", "lact"):
            self.assertIn(package, live)
        for forbidden in ("firefox", "flatpak", "snapd", "docker", "preload", "prelink"):
            self.assertNotIn(forbidden, live)
            self.assertNotIn(forbidden, installed)

    def test_graphics_are_hardware_neutral(self):
        forbidden = {"linux-cachyos-nvidia-open", "linux-cachyos-lts-nvidia-open",
                     "nvidia-utils", "lib32-vulkan-intel", "lib32-vulkan-radeon"}
        live = set((REPO / "archiso/packages_desktop.x86_64").read_text().splitlines())
        installed = set(MANIFEST.read_text().splitlines())
        for packages in (live, installed):
            self.assertFalse(forbidden & packages)
            for item in ("vulkan-swrast", "lib32-vulkan-swrast",
                         "vulkan-icd-loader", "lib32-vulkan-icd-loader"):
                self.assertIn(item, packages)
        assistant = (LIVE / "usr/local/bin/skaldr-gpu-assistant").read_text()
        self.assertIn("pkexec chwd -a", assistant)
        self.assertNotIn("nvidia-dkms-580xx nvidia-dkms-470xx", assistant)

    def test_live_session_avoids_locking_during_installation(self):
        profile = PROFILE.read_text()
        self.assertIn('configure_live_screen_lock()', profile)
        self.assertIn('sys.argv[1] == "live"', profile)
        self.assertIn('config.set("Daemon", "Autolock", "false")', profile)
        self.assertIn('config.set("Daemon", "LockOnResume", "false")', profile)
        self.assertIn('config.set("Daemon", "LockOnStart", "false")', profile)
        # Defaults for installed users must stay locked and password-protected.
        installed_default = (LIVE / "etc/skel/.config/kscreenlockerrc").read_text()
        self.assertIn("Autolock=true", installed_default)
        self.assertIn("LockOnResume=true", installed_default)

    def test_first_login_autostart_replaces_upstream_greeting(self):
        script = LIVE / "usr/local/bin/skaldr-postinstall"
        setup = runpy.run_path(str(script), run_name="skaldr_test")["setup_user_autostart"]
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp) / "testuser"
            autostart = home / ".config/autostart"
            autostart.mkdir(parents=True)
            cachy = autostart / "cachyos-hello.desktop"
            cachy.write_text("[Desktop Entry]\nName=CachyOS Hello\nExec=cachyos-hello\n")
            welcome = Path(tmp) / "skaldr-welcome.desktop"
            welcome.write_text("[Desktop Entry]\nExec=/usr/local/bin/skaldr-welcome --startup\n")
            with patch("os.chown") as mocked:
                setup(home, 1000, 1000, welcome)
            self.assertIn("Hidden=true", cachy.read_text())
            self.assertEqual((autostart / "skaldr-welcome.desktop").read_text(),
                             welcome.read_text())
            self.assertEqual(mocked.call_count, 3)
        self.assertIn("configure_installed_users()", script.read_text())
        self.assertIn("--startup", (LIVE / "etc/xdg/autostart/skaldr-welcome.desktop").read_text())
        self.assertIn("time.sleep(8)", (LIVE / "usr/local/bin/skaldr-welcome").read_text())

    def test_quicktest_shell_syntax(self):
        script = REPO / "testcases/cachyos/dailylive/test_install_calamares"
        result = subprocess.run(["bash", "-n", str(script)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        source = script.read_text()
        self.assertEqual(source.count("function test_input_validation()"), 1)
        self.assertIn('grep -aFq', source)
        bios = REPO / "testcases/cachyos/dailylive/test_live_bios"
        result = subprocess.run(["bash", "-n", str(bios)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Launch installer", bios.read_text())
        self.assertIn("OVMF", bios.read_text())
        self.assertIn("function test_setup()", bios.read_text())
        self.assertIn("function test_live_bios()", bios.read_text())

    def test_numlock_and_installer(self):
        self.assertEqual((LIVE / "etc/xdg/kcminputrc").read_text(), "[Keyboard]\nNumLock=0\n")
        self.assertFalse((LIVE / "etc/skel/.config/kcminputrc").exists())
        numlock = (LIVE / "usr/local/bin/skaldr-numlock").read_text()
        self.assertIn('install -m 0644 "$source_file"', numlock)
        self.assertIn('install -d -m 0755 -o "$user" -g "$group" "$home/.config"', numlock)
        self.assertIn('plasma-login-wallpaperrc', numlock)
        self.assertFalse((LIVE / "usr/local/bin/skaldr-capslock").exists())
        self.assertFalse((LIVE / "etc/xdg/autostart/skaldr-capslock.desktop").exists())
        self.assertIn("skaldr-numlock", INJECT.read_text())
        # This file belongs to cachyos-kde-settings: early copying breaks pacman.
        self.assertNotIn('"/etc/skel/.config/kcminputrc",', INJECT.read_text())
        postinstall = (LIVE / "usr/local/bin/skaldr-postinstall").read_text()
        self.assertIn('call("/usr/local/bin/skaldr-numlock")', postinstall)
        self.assertLess(postinstall.index('call("pacman", "-Syu"'),
                        postinstall.index('call("/usr/local/bin/skaldr-numlock")'))
        installer = (LIVE / "usr/local/bin/calamares-online.sh").read_text()
        self.assertIn("sudo /usr/local/bin/skaldr-cal-inject", installer)
        self.assertNotIn("exit 1\\n", installer)

    def test_live_uses_executable_permissions_for_all_skaldr_scripts(self):
        # mkarchiso overwrites Git's mode 100755 with 0644 unless the
        # overlay executable is explicitly listed in profiledef.sh.
        profile = (REPO / "archiso/profiledef.sh").read_text()
        helpers = list((LIVE / "usr/local/bin").glob("skaldr-*"))
        self.assertGreaterEqual(len(helpers), 10)
        for helper in helpers:
            if helper.is_file() and helper.stat().st_mode & 0o111:
                entry = f'["/usr/local/bin/{helper.name}"]="0:0:755"'
                self.assertIn(entry, profile, "Non-executable in the ISO: " + helper.name)
        self.assertIn('["/usr/local/bin/pkexec-wrapper"]="0:0:755"', profile)

    def test_pinned_calamares_rebuild_and_local_repo(self):
        script = (REPO / "scripts/skaldr-build-calamares.sh").read_text()
        self.assertIn("199d71543db805fac2cc649ced72ad01dcb2c362", script)
        self.assertIn("288a24812b36c68bf16657e8131d00351878f3e0", script)
        self.assertIn("makepkg --config", script)
        self.assertIn('CFLAGS+=" -march=x86-64 -mtune=generic"', script)
        self.assertIn('CXXFLAGS+=" -march=x86-64 -mtune=generic"', script)
        self.assertIn("repo-add", script)
        self.assertIn("libboost_python314.so.1.91.0", script)
        self.assertNotIn("ln -s", script)
        helper = (REPO / "scripts/skaldr-stage-calamares-repo.py").read_text()
        self.assertIn("[skaldr-local]", helper)
        self.assertIn("config.write_text", helper)
        self.assertNotIn("[skaldr-local]", (REPO / "archiso/pacman.conf").read_text())
        workflow = (REPO / ".github/workflows/build.yml").read_text()
        self.assertIn("Rebuild Calamares against current Boost libraries", workflow)
        self.assertIn('SKALDR_CALAMARES_REPO="$GITHUB_WORKSPACE/.skaldr-local"', workflow)
        self.assertIn("scripts/skaldr-stage-calamares-repo.py", (REPO / "util-iso.sh").read_text())

    def test_installer_starts_without_reinstalling_live_packages(self):
        installer = (LIVE / "usr/local/bin/calamares-online.sh").read_text()
        self.assertIn("set -Eeuo pipefail", installer)
        self.assertIn('stage="start Calamares GUI"', installer)
        self.assertIn("pkexec-wrapper calamares -D6", installer)
        self.assertIn("sudo /usr/local/bin/skaldr-cal-inject", installer)
        self.assertIn("kdialog --title", installer)
        self.assertIn("logger -t skaldr-installer", installer)
        self.assertIn("pacstrap.conf", installer)
        self.assertIn("shellprocess.conf", installer)
        for forbidden in ("sudo rm -rf /etc/pacman.d/gnupg",
                          "sudo pacman -Sy", "pacman-key --init"):
            self.assertNotIn(forbidden, installer)

    def test_branding_and_controls(self):
        release = (LIVE / "etc/os-release").read_text()
        self.assertIn('NAME="Skaldr OS"', release)
        profile = (REPO / "archiso/profiledef.sh").read_text()
        self.assertIn('iso_name="skaldr"', profile)
        self.assertIn("SKALDR_", profile)
        for name in ("skaldr-doctor", "skaldr-center"):
            self.assertTrue((LIVE / "usr/local/bin" / name).is_file())
        injector = INJECT.read_text()
        self.assertIn("/usr/share/skaldr/os-release", injector)
        self.assertIn("/usr/local/bin/skaldr-center", injector)
        cleanup = (LIVE / "usr/local/bin/removeun").read_text()
        self.assertNotIn("pacman -Rsnc", cleanup)

    def test_snapshots_and_thermal_checks(self):
        profile = PROFILE.read_text()
        self.assertIn('fs.stdout.strip() != "btrfs"', profile)
        self.assertIn('"snapper-cleanup.timer"', profile)
        self.assertIn('"snapper", "--no-dbus", "-c", "root", "get-config"', profile)
        self.assertIn('"create-config", "/"', profile)
        self.assertIn('"snapper-timeline.timer"', profile)
        doctor = (LIVE / "usr/local/bin/skaldr-doctor").read_text()
        self.assertIn('"highest_sensor_temperature_celsius"', doctor)
        for name in ("snapper", "snap-pac", "smartmontools"):
            self.assertIn(name, (REPO / "archiso/packages_desktop.x86_64").read_text().splitlines())

    def test_iso_output_uses_skaldr_name(self):
        script = (REPO / 'util-iso.sh').read_text()
        self.assertIn('vars+=("skaldr")', script)
        self.assertIn('built_iso=', script)
        self.assertNotIn('source "${work_dir}/archiso/profiledef.sh"', script)
        self.assertIn('iso_name="$(sed -n ', script)
        self.assertIn('iso_arch="$(sed -n ', script)
        self.assertNotIn('mv "$outFolder/$_profile/cachyos-', script)
        self.assertNotIn("occt", (REPO / "archiso/packages_desktop.x86_64").read_text().splitlines())

    def test_versioning_and_first_login(self):
        version_script = REPO / "scripts/skaldr-version.py"
        self.assertEqual((REPO / "VERSION").read_text().strip(), "0.1.0")
        self.assertIn("FORK_POINT", version_script.read_text())
        result = subprocess.run([sys.executable, str(version_script), "--json"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        import json
        data = json.loads(result.stdout)
        self.assertRegex(data["version"], r"^0\.1\.0-dev\.\d+\+g[0-9a-f]{8}$")
        self.assertGreater(data["project_commit_count"], 0)
        self.assertEqual(len(data["git_revision"]), 40)
        self.assertTrue((LIVE / "usr/local/bin/skaldr-welcome").is_file())
        self.assertIn("welcome-shown", (LIVE / "usr/local/bin/skaldr-welcome").read_text())
        self.assertIn("/usr/share/skaldr/build.json", INJECT.read_text())
        # Verify the exact version is prepared in the staged Live image.
        source = (REPO / "util-iso.sh").read_text()
        self.assertIn("--install-to", source)
        self.assertIn('iso_file="skaldr-', source)
        with tempfile.TemporaryDirectory() as tmp:
            template = Path(tmp) / "usr/share/skaldr/os-release"
            template.parent.mkdir(parents=True)
            template.write_text('NAME="Skaldr OS"\nID=arch\n')
            check = subprocess.run([sys.executable, str(version_script),
                                    "--install-to", tmp],
                                   capture_output=True, text=True)
            self.assertEqual(check.returncode, 0, check.stderr)
            self.assertIn('VERSION_ID="0.1.0-dev.',
                          (Path(tmp) / "etc/os-release").read_text())
            self.assertEqual(json.loads((Path(tmp) / "usr/share/skaldr/build.json")
                                        .read_text())["git_revision"], data["git_revision"])

    def test_offline_raven_wallpaper(self):
        import shutil
        source_logo = REPO / "assets/skaldr-logo.png"
        self.assertTrue(source_logo.is_file())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            logo = root / "usr/share/pixmaps/skaldr-logo.png"
            logo.parent.mkdir(parents=True)
            shutil.copyfile(source_logo, logo)
            result = subprocess.run(["bash", str(REPO / "scripts/skaldr-make-wallpaper.sh"), str(root)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            wall = root / "usr/share/wallpapers/Skaldr/contents/images/1920x1080.svg"
            self.assertIn("data:image/png;base64,", wall.read_text())
            self.assertIn("Skaldr OS", wall.read_text())
            self.assertNotIn("https://", wall.read_text())
        t = (LIVE / "usr/local/bin/skaldr-theme").read_text()
        self.assertIn("plasma-apply-wallpaperimage", t)
        self.assertIn("wallpaper-applied", t)
        self.assertIn("skaldr-theme.desktop", INJECT.read_text())

    def test_ci_boot_preflight(self):
        workflow = (REPO / ".github/workflows/build.yml").read_text()
        self.assertIn("Install Git before checkout", workflow)
        self.assertIn("pacman -Syu --noconfirm --needed git", workflow)
        self.assertLess(workflow.index("Install Git before checkout"),
                        workflow.index("Checkout complete Skaldr OS repository history"))
        self.assertIn("fetch-depth: 0", workflow)
        self.assertIn('git -c "safe.directory=$GITHUB_WORKSPACE" cat-file -e 3215497d2e8c5fea90e185affcf973dfa2cf790b', workflow)
        self.assertIn("python3 scripts/skaldr-version.py --json", workflow)
        self.assertIn("bootloader: grub", workflow)
        self.assertIn("filesystem: btrfs", workflow)
        self.assertIn("filesystem: ext4", workflow)
        self.assertIn("bootloader: bios", workflow)
        self.assertIn("filesystem: live", workflow)
        self.assertIn('boot="legacy"', workflow)
        self.assertIn("test_live_bios cachyos dailylive", workflow)
        qt = (REPO / "testcases/cachyos/dailylive/test_install_calamares").read_text()
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "Welcome to Skaldr OS!"', qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "$text_calamares_welcome"', qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Launch installer"', qt)
        vm = (REPO / "machines/cachyos-dailylive.conf").read_text()
        self.assertIn('mouse="tablet"', vm)
        self.assertIn('disk_size="48G"', vm)
        self.assertNotIn('cpu_model="x86-64-v3"', vm)
        self.assertIn('extra_args="-cpu Haswell-v4', vm)
        self.assertNotIn('extra_args="-cpu x86-64-v3', vm)
        self.assertIn('"Haswell-v4"', qt)
        self.assertIn('serial="socket"', vm)
        self.assertIn("-qmp unix:", vm)
        self.assertIn('$(pwd)/cachyos-dailylive/skaldr-ci-qmp.sock', vm)
        self.assertNotIn('$(pwd)/machines/cachyos-dailylive/', vm)
        self.assertIn("python3 scripts/skaldr-qmp-click.py", qt)
        self.assertNotIn('qt_send_command "mouse_move', qt)
        qmp = subprocess.run([sys.executable, str(REPO / "scripts/skaldr-qmp-click.py"),
                              "--x", "704", "--y", "600", "--width", "1408",
                              "--height", "792", "--dry-run"],
                             capture_output=True, text=True)
        self.assertEqual(qmp.returncode, 0, qmp.stderr)
        import json
        point = json.loads(qmp.stdout)
        self.assertTrue(16000 <= point["x"] <= 16800)
        self.assertTrue(24500 <= point["y"] <= 25200)
        self.assertNotIn('qt_send_string_return "/usr/local/bin/calamares-online.sh"', qt)
        self.assertNotIn('qt_send_string_tab "CALAMARES_SKIP_GEOIP=1 sudo', qt)
        self.assertIn("qt_wait_for_seconds 90", qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "You are using a testing ISO" 6 4', qt)
        self.assertIn('qt_send_key "return"', qt)
        self.assertLess(qt.index('You are using a testing ISO'),
                        qt.index('qt_wait_for_text "$FUNCNAME" "$text_calamares_welcome"'))
        self.assertIn('qt_wait_for_text "$FUNCNAME" "$text_calamares_welcome" 12 15', qt)
        self.assertIn('test_ci_cpu_model', qt)
        self.assertIn('Effective QEMU CPU model:', qt)
        self.assertIn('test_installed_system_cold_boot', qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Show On-Screen Keyboard" 30 10', qt)
        self.assertNotIn('qt_wait_for_text "$FUNCNAME" "$test_user" 30 10', qt)
        self.assertIn('QMP login focus failed', qt)
        self.assertIn('test_installed_plasma_first_login', qt)
        self.assertIn('qt_send_string_return "$test_password"', qt)
        self.assertIn('qt_wait_for_text "$FUNCNAME" "Welcome to Skaldr OS" 30 10', qt)
        self.assertIn('qt_launch_quickemu || qt_test_fail', qt)
        self.assertIn('Second boot still has live installer ISO attached', qt)
        self.assertLess(qt.index('test_calamares_finished\n    test_installed_system_cold_boot'),
                        qt.index('test_installed_system_cold_boot\n    test_installed_plasma_first_login'))
        self.assertLess(qt.index('test_installed_plasma_first_login\n    test_power_off_vm'),
                        qt.index('\n}\n\ntest_description', qt.index('function test_install_calamares()')))
        self.assertIn('Skaldr: Btrfs snapshot configuration is available.', workflow)
        self.assertIn('Arch mirror download failed (attempt $attempt/3)', workflow)
        self.assertIn('for attempt in 1 2 3; do', workflow)

    def test_limine_checksum_sync(self):
        # The final initramfs can change after a prior limine.conf was hashed.
        # The repaired hash must match the actual bytes; a missing file fails.
        sync = runpy.run_path(str(PROFILE), run_name="skaldr_profile_test")["sync_limine_checksums"]
        with tempfile.TemporaryDirectory() as tmp:
            boot = Path(tmp)
            image = boot / "disk-id/linux-cachyos/initramfs"
            image.parent.mkdir(parents=True)
            image.write_bytes(b"the actual rebuilt initramfs bytes")
            config = boot / "limine.conf"
            config.write_text(
                "/+Skaldr\n"
                + "  module_path: boot():/disk-id/linux-cachyos/initramfs#"
                + "0" * 128
                + "\n"
            )
            self.assertEqual(sync(config, boot), 1)
            self.assertIn(hashlib.blake2b(image.read_bytes()).hexdigest(),
                          config.read_text())
            self.assertEqual(sync(config, boot), 0)
            image.unlink()
            with self.assertRaisesRegex(RuntimeError, "missing boot file"):
                sync(config, boot)

    def test_policy(self):
        profile = PROFILE.read_text()
        self.assertIn('vm.swappiness = 0', profile)
        self.assertIn('default_sched = "scx_lavd"', profile)
        self.assertIn('default_mode = "Gaming"', profile)
        self.assertIn('performance', profile.lower())
        self.assertIn('mitigations=off', profile)
        self.assertIn('check_limine_integrity()', profile)
        self.assertIn('sync_limine_checksums()', profile)
        self.assertIn('limine-enroll-config', profile)
        self.assertIn('hashlib.blake2b()', profile)
        self.assertIn('"limine-update"', profile)
        self.assertIn('os.geteuid()', profile)

    def test_live_boot(self):
        for path in BOOT:
            self.assertIn("mitigations=off", path.read_text(), str(path))
        grub = BOOT[0].read_text()
        fallback = grub.split("menuentry \"Skaldr OS Legacy Hardware")[1].split("menuentry ")[0]
        self.assertNotIn("mitigations=off", fallback, "Emergency fallback must stay usable")

    @unittest.skipIf(yaml is None, "PyYAML is not available")
    def test_calamares_hook(self):
        for with_i18n in (True, False):
            with self.subTest(with_i18n=with_i18n):
                with tempfile.TemporaryDirectory() as d:
                    root = Path(d)
                    pacstrap = root / "pacstrap.conf"
                    process = root / "shellprocess.conf"
                    pacstrap.write_text('---\nbasePackages:\n - base\npostInstallFiles:\n - "/etc/mkinitcpio.conf"\n')
                    suffix = '\ni18n:\n  name: "Cleanup"\n' if with_i18n else ''
                    process.write_text('---\ndontChroot: false\nscript:\n  - command: "/usr/local/bin/dmcheck"\n' + suffix)
                    env = dict(os.environ, SKALDR_CALAMARES_MODULES=d)
                    for _ in range(2):
                        completed = subprocess.run([sys.executable, str(INJECT)],
                            env=env, capture_output=True, text=True)
                        self.assertEqual(completed.returncode, 0, completed.stderr)
                    p = yaml.safe_load(pacstrap.read_text())
                    s = yaml.safe_load(process.read_text())
                    self.assertIn("/usr/local/bin/skaldr-postinstall", p["postInstallFiles"])
                    self.assertIn("/etc/systemd/system/skaldr-performance.service", p["postInstallFiles"])
                    self.assertNotIn("/etc/skel/.config/kcminputrc", p["postInstallFiles"])
                    steps = [v.get("command") for v in s["script"] if isinstance(v, dict)]
                    self.assertEqual(steps.count("/usr/local/bin/skaldr-postinstall"), 1)
                    self.assertEqual(steps[0], "/usr/local/bin/dmcheck")

if __name__ == "__main__":
    unittest.main()
