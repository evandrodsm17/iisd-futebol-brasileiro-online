import tempfile
import unittest
from pathlib import Path
from audit_charge_graphics_overlap import audit


class GraphicsOverlapTests(unittest.TestCase):
    def test_matches_and_missing_files(self):
        runs={'runs':[{'samples':[{'descriptor':123}]}]}
        records=[{'frame':5,'actor':{'descriptor':123},'vram':'vram.bin'},
                 {'actor':{'descriptor':456}}]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'vram.bin').write_bytes(b'x')
            report=audit(runs,records,root)
            self.assertEqual(report['snapshots_examined'],2)
            self.assertEqual(len(report['matches']),1)
            self.assertTrue(report['matches'][0]['files_present']['vram'])
            self.assertFalse(report['matches'][0]['files_present']['cgram'])


if __name__=='__main__': unittest.main()
