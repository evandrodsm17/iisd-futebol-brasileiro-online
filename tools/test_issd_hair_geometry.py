import json
from pathlib import Path
import unittest
from extract_issd_hair_geometry import build

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
SNAPSHOT=ROOT/'analysis'/'bsnes-hair-geometry'/'geometry.jsonl'
SCRIPTS=ROOT/'dist'/'data'/'issd-locomotion-scripts.json'


@unittest.skipUnless(ROM.exists() and SNAPSHOT.exists(), 'Requires local ROM and private emulator snapshot')
class HairGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM.read_bytes()
        cls.scripts=json.loads(SCRIPTS.read_text(encoding='utf8'))
        cls.rows=[json.loads(line) for line in SNAPSHOT.read_text(encoding='utf8').splitlines()]

    def test_all_geometry_matches_runtime(self):
        result=build(self.rom,self.scripts,self.rows)
        self.assertEqual((result['snapshot_entries_verified'],result['unique_descriptors']),(167,90))
        self.assertEqual(result['poses'][str(0xa749)]['pointer'],0x4f2c)

    def test_mismatch_and_incomplete_snapshot_rejected(self):
        changed=[dict(row) for row in self.rows]
        changed[0]['x_word']^=1
        with self.assertRaisesRegex(ValueError,'Geometry mismatch'):
            build(self.rom,self.scripts,changed)
        with self.assertRaises(ValueError):
            build(self.rom,self.scripts,self.rows[:-1])


if __name__=='__main__':unittest.main()
