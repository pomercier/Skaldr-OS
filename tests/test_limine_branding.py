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
    def test_missing_root_in_modern_group_fails(self):
        self.create(modern=section('Skaldr OS','quiet mitigations=off'))
        with self.assertRaisesRegex(RuntimeError,'no verified root'):
            lib.reconcile_limine_menu(self.root)
        self.assertIn('/+CachyOS',self.cfg.read_text())
    def test_difference_in_cmdline_is_not_pruned(self):
        self.create(legacy=section('CachyOS',CMD+' foo=bar'))
        self.assertEqual(lib.reconcile_limine_menu(self.root),'legacy-preserved-unverified')
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
    def test_snapshot_lines_preserved_byte_exactly(self):
        self.create()
        lib.reconcile_limine_menu(self.root)
        self.assertIn(SNAP, self.cfg.read_text())
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
