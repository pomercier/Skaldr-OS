from pathlib import Path
import importlib.util
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'archiso/airootfs/usr/local/lib/skaldr/limine_branding.py'
spec = importlib.util.spec_from_file_location('limine_branding', MODULE)
lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lib)

UUID = 'e7fdc772-9edc-4ffa-bdca-c3ca49ff1572'
CMD = f'quiet nowatchdog rw rootflags=subvol=/@ root=UUID={UUID}'
SAME = f'{CMD} mitigations=off'

def section(name, params, first='linux-cachyos', hashes='same'):
    return (f'/+{name}\n'
            f'//{first}\n'
            '    protocol: linux\n'
            f'    path: boot():/uuid/{first}#deadbeef{hashes}\n'
            f'    cmdline: {params}\n'
            f'    module_path: boot():/uuid/{first}/initramfs#{hashes}\n'
            f'//{first}-lts\n'
            '    protocol: linux\n'
            f'    path: boot():/uuid/{first}-lts#cafebabe{hashes}\n'
            f'    cmdline: {params}\n'
            f'    module_path: boot():/uuid/{first}-lts/initramfs#{hashes}\n')

SNAP = ('/+Snapshots\n'
        '///10/snapshot\n    protocol: linux\n    path: boot():/uuid/snap\n'
        '    cmdline: mitigations=off rootflags=subvol=/@/.snapshots/10/snapshot\n')
EFI = '/EFI fallback\n    protocol: efi\n    path: boot():/EFI/BOOT/BOOTX64.EFI\n'

class BrandingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'boot').mkdir()
        (self.root / 'etc/default').mkdir(parents=True)
        (self.root / 'etc/default/limine').write_text('ESP_PATH="/boot"\n')
        self.snap = self.root / 'etc/limine-snapper-sync.conf'
        self.snap.write_text('# snapshot config\n')
        self.cfg = self.root / 'boot/limine.conf'
    def create(self, *, legacy=None, modern=None, snapshots=SNAP):
        old = section('CachyOS', CMD) if legacy is None else legacy
        new = section('Skaldr OS', SAME) if modern is None else modern
        self.cfg.write_text('timeout: 5\ndefault_entry: 2\nremember_last_entry: yes\n'+old+new+snapshots+EFI)
    def test_duplicate_identical_images_pruned(self):
        self.create()
        status = lib.reconcile_limine_menu(self.root)
        self.assertEqual(status,'legacy-duplicate-removed')
        text = self.cfg.read_text()
        self.assertNotIn('/+CachyOS\n', text)
        self.assertIn('/+Skaldr OS\n', text)
        self.assertIn('default_entry: Skaldr OS/linux-cachyos',text)
        self.assertIn('interface_branding: SKALDR OS', text)
        self.assertIn('/+Snapshots\n', text)
        self.assertIn(EFI,text)
        self.assertIn('TARGET_OS_NAME="Skaldr OS"',self.snap.read_text())
    def test_idempotent(self):
        self.create()
        lib.reconcile_limine_menu(self.root)
        first=self.cfg.read_text()
        self.assertEqual(lib.reconcile_limine_menu(self.root),'already-skaldr')
        self.assertEqual(first,self.cfg.read_text())
    def test_mismatched_kernel_hash_preserves_legacy(self):
        self.create(legacy=section('CachyOS',CMD,hashes='old'))
        self.assertEqual(lib.reconcile_limine_menu(self.root),'legacy-preserved-unverified')
        self.assertIn('/+CachyOS',self.cfg.read_text())
        self.assertIn('default_entry: 2',self.cfg.read_text())
        self.assertNotIn('TARGET_OS_NAME=',self.snap.read_text())
    def test_missing_root_in_modern_group_recovered_from_matching_fallback(self):
        self.create(modern=section('Skaldr OS','mitigations=off'))
        status = lib.reconcile_limine_menu(self.root)
        self.assertEqual(status, "legacy-duplicate-removed")
        text = self.cfg.read_text()
        self.assertNotIn('/+CachyOS', text)
        self.assertIn('default_entry: Skaldr OS/linux-cachyos', text)
        self.assertEqual(text.count('root=UUID=' + UUID), 2)
        self.assertEqual(text.count('rootflags=subvol=/@ '), 2)
        self.assertIn(SNAP, text)
        self.assertIn(EFI, text)
        self.assertEqual(lib.reconcile_limine_menu(self.root), "already-skaldr")

    def test_mismatched_new_images_preserve_rooted_legacy_fallback(self):
        self.create(legacy=section('CachyOS',CMD,hashes='different'),
                    modern=section('Skaldr OS','mitigations=off'))
        self.snap.write_text('TARGET_OS_NAME="CachyOS"\n')
        status = lib.reconcile_limine_menu(self.root)
        self.assertEqual(status, "legacy-preserved-rootless")
        revised = self.cfg.read_text()
        self.assertIn('/+CachyOS', revised)
        self.assertIn('/+Skaldr OS', revised)
        self.assertIn('default_entry: CachyOS/linux-cachyos', revised)
        self.assertIn(SNAP, revised)
        self.assertIn(EFI, revised)
        self.assertIn('TARGET_OS_NAME="CachyOS"', self.snap.read_text())
        self.assertEqual(lib.reconcile_limine_menu(self.root), status)

    def test_inconsistent_fallback_roots_rejected(self):
        bad = section('CachyOS',CMD).replace('root=UUID='+UUID,
                                               'root=UUID=other', 1)
        self.create(legacy=bad, modern=section('Skaldr OS','mitigations=off'))
        before = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.cfg.read_text(), before)

    def test_recovery_rejects_conflicting_existing_modern_root(self):
        modern = section('Skaldr OS', 'mitigations=off')
        modern = modern.replace('cmdline: mitigations=off',
                                'cmdline: mitigations=off root=UUID=wrong', 1)
        self.create(modern=modern)
        original = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(original, self.cfg.read_text())

    def test_recovery_rejects_modern_subvolume_disagreement(self):
        modern = section('Skaldr OS', 'mitigations=off')
        modern = modern.replace('cmdline: mitigations=off',
                                'cmdline: mitigations=off rootflags=subvol=/other', 1)
        self.create(modern=modern)
        original = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(original, self.cfg.read_text())

    def test_no_legacy_rootflags_mismatch_between_kernels(self):
        different = section('CachyOS',CMD).replace('rootflags=subvol=/@',
                                                     'rootflags=subvol=/old', 1)
        self.create(legacy=different,
                    modern=section('Skaldr OS','mitigations=off'))
        with self.assertRaisesRegex(RuntimeError,'no safe fallback'):
            lib.reconcile_limine_menu(self.root)

    def test_missing_root_in_both_groups_fails_without_changes(self):
        self.create(legacy=section('CachyOS','quiet nowatchdog'),
                    modern=section('Skaldr OS','mitigations=off'))
        before = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.cfg.read_text(), before)

    def test_unverified_rootless_kernel_option_refused(self):
        self.create(modern=section('Skaldr OS','mitigations=off init=/bin/false'))
        before = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.cfg.read_text(), before)

    def test_missing_root_without_legacy_group_fails_without_changes(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off'))
        before = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.cfg.read_text(), before)

    def test_partial_missing_root_recovers_only_verified_entry(self):
        modern = section('Skaldr OS', 'mitigations=off')
        modern = modern.replace('    cmdline: mitigations=off', '    cmdline: '+SAME, 1)
        self.create(modern=modern)
        self.assertEqual(lib.reconcile_limine_menu(self.root), 'legacy-duplicate-removed')
        lines = self.cfg.read_text()
        self.assertEqual(lines.count('root=UUID=' + UUID), 2)

    def test_difference_in_cmdline_is_not_pruned(self):
        self.create(legacy=section('CachyOS',CMD+' foo=bar'))
        self.assertEqual(lib.reconcile_limine_menu(self.root),'legacy-preserved-unverified')
    def create_fstab(self, source=None, options="rw,compress=zstd:3,subvol=/@"):
        target = self.root / 'etc/fstab'
        target.write_text((source or 'UUID='+UUID) + ' / btrfs ' + options + ' 0 0\n')
        return target

    def test_calamares_fstab_repairs_different_initramfs_hashes(self):
        self.create(legacy=section('CachyOS', CMD, hashes='upstream'),
                    modern=section('Skaldr OS','mitigations=off', hashes='new'))
        self.create_fstab()
        result = lib.reconcile_limine_menu(self.root)
        self.assertEqual(result, 'legacy-preserved-verified-skaldr')
        fixed = self.cfg.read_text()
        self.assertIn('/+CachyOS\n', fixed)
        self.assertIn('/+Skaldr OS\n', fixed)
        self.assertIn('default_entry: Skaldr OS/linux-cachyos', fixed)
        self.assertEqual(fixed.count('root=UUID='+UUID), 4)
        self.assertIn(SNAP, fixed)
        self.assertIn(EFI, fixed)
        self.assertIn('TARGET_OS_NAME="Skaldr OS"',self.snap.read_text())

    def test_real_cachyos_kernel_flags_repaired_from_fstab(self):
        # The Limine entry tool emits additional flags that must not prevent
        # recovery of the actual Calamares-installed root and Btrfs subvolume.
        params = ("BOOT_IMAGE=/@/boot/vmlinuz-linux-cachyos "
                  "quiet loglevel=3 zswap.enabled=0 nvme_load=YES "
                  "nowatchdog rw mitigations=off")
        self.create(legacy='', modern=section('Skaldr OS', params))
        self.create_fstab()
        self.assertEqual(lib.reconcile_limine_menu(self.root), 'already-skaldr')
        updated = self.cfg.read_text()
        self.assertEqual(updated.count('root=UUID=' + UUID), 2)
        self.assertIn('zswap.enabled=0 nvme_load=YES', updated)

    def test_existing_equivalent_btrfs_subvolume_spelling_accepted(self):
        self.create(legacy='', modern=section(
            'Skaldr OS', 'quiet rootflags=subvol=@ mitigations=off'))
        self.create_fstab()
        self.assertEqual(lib.reconcile_limine_menu(self.root), 'already-skaldr')
        self.assertEqual(self.cfg.read_text().count('root=UUID=' + UUID), 2)

    def test_fstab_recovery_rejects_emergency_boot_override(self):
        self.create(legacy='', modern=section(
            'Skaldr OS', 'quiet systemd.unit=emergency.target'))
        self.create_fstab()
        unchanged = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(unchanged, self.cfg.read_text())

    def test_fstab_root_repairs_without_legacy_group(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off'))
        self.create_fstab()
        self.assertEqual(lib.reconcile_limine_menu(self.root), 'already-skaldr')
        self.assertEqual(self.cfg.read_text().count('root=UUID='+UUID), 2)

    def test_fstab_repair_keeps_safety_on_repeated_runs(self):
        self.create(modern=section('Skaldr OS','mitigations=off'))
        self.create_fstab()
        initial = lib.reconcile_limine_menu(self.root)
        after = self.cfg.read_text()
        self.assertIn(initial, ('legacy-duplicate-removed','legacy-preserved-verified-skaldr'))
        self.assertEqual(lib.reconcile_limine_menu(self.root),
                         'already-skaldr' if initial == 'legacy-duplicate-removed'
                         else 'legacy-preserved-unverified')
        self.assertEqual(self.cfg.read_text(), after)

    def test_rejects_untrusted_fstab_uuid_without_safe_fallback(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off'))
        self.create_fstab(source="UUID=not-a-real-uuid")
        original = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.cfg.read_text(), original)

    def test_rejects_mismatched_subvolume_from_fstab(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off'))
        self.create_fstab(options="rw,subvol=/other")
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)

    def test_rejects_duplicate_root_mounts_in_fstab(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off'))
        fstab = self.create_fstab()
        fstab.write_text(fstab.read_text()*2)
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)

    def test_fstab_cannot_override_explicit_conflicting_root(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off root=UUID=wrong'))
        self.create_fstab()
        original = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'conflict with installed Btrfs fstab'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(original, self.cfg.read_text())

    def test_fstab_rejects_fully_populated_wrong_subvolume(self):
        self.create(legacy='', modern=section(
            'Skaldr OS',f'mitigations=off root=UUID={UUID} rootflags=subvol=/other'))
        self.create_fstab()
        original = self.cfg.read_text()
        with self.assertRaisesRegex(RuntimeError, 'conflict with installed Btrfs fstab'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(original, self.cfg.read_text())

    def test_fstab_does_not_accept_unknown_init_override(self):
        self.create(legacy='', modern=section('Skaldr OS','mitigations=off init=/bin/false'))
        self.create_fstab()
        with self.assertRaisesRegex(RuntimeError, 'no safe fallback'):
            lib.reconcile_limine_menu(self.root)

    def test_no_limine_system_untouched(self):
        (self.root / 'etc/default/limine').unlink()
        self.create()
        before=self.cfg.read_text()
        self.assertEqual(lib.reconcile_limine_menu(self.root),'not-limine')
        self.assertEqual(self.cfg.read_text(),before)
    def test_missing_skaldr_group_preserves_fallback(self):
        self.create(modern='')
        self.assertEqual(lib.reconcile_limine_menu(self.root),'no-skaldr-group')
        self.assertIn('/+CachyOS',self.cfg.read_text())
    def test_no_secondary_snapshot_config_created(self):
        self.create()
        self.snap.unlink()
        lib.reconcile_limine_menu(self.root)
        self.assertFalse(self.snap.exists())
    def test_explicit_cachyos_snapper_target_migrated(self):
        self.create()
        self.snap.write_text('TARGET_OS_NAME="CachyOS"\nKEEP=1\n')
        lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.snap.read_text(),'TARGET_OS_NAME="Skaldr OS"\nKEEP=1\n')
    def test_custom_snapshot_target_preserved(self):
        self.create()
        self.snap.write_text('TARGET_OS_NAME="Other OS"\n')
        lib.reconcile_limine_menu(self.root)
        self.assertEqual(self.snap.read_text(),'TARGET_OS_NAME="Other OS"\n')
    def test_ambiguous_snapper_preflight_makes_no_boot_changes(self):
        self.create()
        self.snap.write_text('TARGET_OS_NAME="CachyOS"\nTARGET_OS_NAME="Other"\n')
        before = self.cfg.read_text()
        with self.assertRaisesRegex(ValueError, 'Duplicate TARGET_OS_NAME'):
            lib.reconcile_limine_menu(self.root)
        self.assertEqual(before, self.cfg.read_text())
    def test_new_root_override_preserves_legacy_fallback(self):
        self.create(modern=section('Skaldr OS',SAME+' root=UUID=elsewhere'))
        with self.assertRaisesRegex(RuntimeError, 'exactly one root'):
            lib.reconcile_limine_menu(self.root)
        self.assertIn('/+CachyOS', self.cfg.read_text())

    def test_unverified_new_kernel_flag_preserves_legacy_fallback(self):
        self.create(modern=section('Skaldr OS',SAME+' init=/bin/false'))
        self.assertEqual(lib.reconcile_limine_menu(self.root), 'legacy-preserved-unverified')
        self.assertIn('/+CachyOS',self.cfg.read_text())

    def test_empty_global_does_not_consume_menu_section(self):
        self.create()
        self.cfg.write_text('interface_branding:\n' + self.cfg.read_text())
        lib.reconcile_limine_menu(self.root)
        self.assertIn('/+Skaldr OS\n',self.cfg.read_text())

    def test_symlinked_config_rejected(self):
        self.create()
        self.cfg.unlink()
        self.cfg.symlink_to(self.root / 'outside')
        with self.assertRaisesRegex(RuntimeError,'unsafe symlink'):
            lib.reconcile_limine_menu(self.root)
    def test_duplicate_sections_rejected(self):
        self.create()
        with self.cfg.open('a') as out:out.write(section('Skaldr OS',SAME))
        with self.assertRaisesRegex(RuntimeError,'Ambiguous duplicate'):
            lib.reconcile_limine_menu(self.root)
    def test_multiple_global_properties_rejected(self):
        self.create()
        self.cfg.write_text('default_entry: 3\n'+self.cfg.read_text())
        with self.assertRaisesRegex(ValueError,'Duplicate global'):
            lib.reconcile_limine_menu(self.root)
    def test_ci_checks_fallback_or_skaldr_and_cold_boot(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/build.yml").read_text()
        self.assertIn('legacy-preserved-rootless', workflow)
        self.assertIn('test_installed_system_cold_boot',
                      (Path(__file__).resolve().parents[1] /
                       'testcases/cachyos/dailylive/test_install_calamares').read_text())

    def test_snapshot_lines_preserved_byte_exactly(self):
        self.create()
        lib.reconcile_limine_menu(self.root)
        self.assertIn(SNAP, self.cfg.read_text())
    def test_ci_requires_installed_limine_menu_reconciliation(self):
        workflow = (Path(__file__).resolve().parents[1] /
                    ".github/workflows/build.yml").read_text()
        self.assertIn("Skaldr: Limine menu reconciliation: (legacy-duplicate-removed|already-skaldr|legacy-preserved-rootless|legacy-preserved-verified-skaldr)", workflow)
        self.assertIn('"${{ matrix.bootloader }}" = "limine"', workflow)

    def test_limine_efi_fallback_preserved(self):
        self.create()
        lib.reconcile_limine_menu(self.root)
        self.assertIn(EFI, self.cfg.read_text())
    def test_missing_snapper_same_menu_still_works(self):
        self.create()
        self.snap.unlink()
        self.assertEqual(lib.reconcile_limine_menu(self.root),'legacy-duplicate-removed')
    def test_snapshot_symlink_safe(self):
        self.create()
        self.snap.unlink()
        self.snap.symlink_to(self.root / 'elsewhere')
        self.assertEqual(lib.reconcile_limine_menu(self.root),'legacy-duplicate-removed')

if __name__=='__main__':unittest.main()
