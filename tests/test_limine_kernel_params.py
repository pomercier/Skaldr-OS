import unittest
from pathlib import Path
import runpy
PROFILE = Path(__file__).resolve().parents[1] / "archiso/airootfs/usr/local/bin/skaldr-profile"
merge = runpy.run_path(str(PROFILE), run_name="test")["ensure_limine_mitigations"]

class TestLimineMerge(unittest.TestCase):
    def test_calamares_append_preserves_uuid_subvolume(self):
        x = ['ESP_PATH="/boot"', 'KERNEL_CMDLINE[default]+="quiet rw rootflags=subvol=/@ root=UUID=abc"']
        y = merge(x)
        self.assertIn('root=UUID=abc', y[1])
        self.assertIn('rootflags=subvol=/@', y[1])
        self.assertTrue(y[1].startswith('KERNEL_CMDLINE[default]+='))
        self.assertIn('mitigations=off', y[1])
        self.assertEqual(len(y),2)

    def test_standard_assignment_retains_content(self):
        self.assertEqual(merge(['KERNEL_CMDLINE[default]="quiet root=PARTUUID=123"']),
                         ['KERNEL_CMDLINE[default]="quiet root=PARTUUID=123 mitigations=off"'])

    def test_already_present_is_idempotent(self):
        original = ['KERNEL_CMDLINE[default]+="quiet mitigations=off rootflags=subvol=/@"']
        self.assertEqual(merge(merge(original[:])), original)

    def test_no_default_uses_append_not_destructive_equals(self):
        self.assertEqual(merge(['ESP_PATH="/boot"'])[-1],
                         'KERNEL_CMDLINE[default]+="mitigations=off"')

    def test_does_not_touch_kernel_specific_keys(self):
        text = 'KERNEL_CMDLINE["linux-cachyos"]="root=UUID=x"'
        self.assertEqual(merge([text])[0],text)

    def test_bad_format_fails_closed(self):
        for raw in ('KERNEL_CMDLINE[default]+="root=UUID=abc" # note',
                    ' KERNEL_CMDLINE[default]="foo"',
                    'KERNEL_CMDLINE[default]=some-variable'):
            with self.subTest(raw=raw),self.assertRaisesRegex(RuntimeError,'Unrecognized'):
                merge([raw])

    def test_repairs_old_skaldr_assignment_that_overrode_rootflags(self):
        arr = ['KERNEL_CMDLINE[default]+="rw rootflags=subvol=/@ root=UUID=123"',
               'KERNEL_CMDLINE[default]="mitigations=off"']
        got = merge(arr)
        self.assertEqual(len(got), 1)
        self.assertIn('rootflags=subvol=/@', got[0])
        self.assertIn('root=UUID=123', got[0])
        self.assertIn('mitigations=off', got[0])

    def test_other_override_of_rootflags_fails_closed(self):
        arr = ['KERNEL_CMDLINE[default]+="root=UUID=123 rootflags=subvol=/@"',
               'KERNEL_CMDLINE[default]="quiet splash"']
        with self.assertRaisesRegex(RuntimeError, 'overrides root'):
            merge(arr)

    def test_multiple_defaults_only_one_new_flag(self):
        arr=['KERNEL_CMDLINE[default]="quiet"',
             'KERNEL_CMDLINE[default]+="root=UUID=y rootflags=subvol=/@"']
        got=merge(arr)
        self.assertEqual(sum(line.count('mitigations=off') for line in got),1)
        self.assertIn('rootflags=subvol=/@',got[-1])

if __name__=='__main__': unittest.main()
