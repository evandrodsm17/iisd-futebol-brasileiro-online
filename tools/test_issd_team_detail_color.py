from pathlib import Path
import unittest
from extract_issd_team_detail_colors import extract
from audit_issd_team_detail_color import audit

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
CAPTURE=ROOT/'analysis'/'bsnes-hair-palette-team'


@unittest.skipUnless(ROM.exists() and (CAPTURE/'hair-runtime.jsonl').exists(),'Requires local ROM and private capture')
class TeamDetailColorTest(unittest.TestCase):
    def test_table_and_runtime(self):
        rom=ROM.read_bytes();result=extract(rom)
        self.assertEqual(len(result['teams']),36)
        self.assertEqual(result['teams'][2]['home'],{'selector':4,'bgr555':0x7800})
        self.assertEqual(result['teams'][2]['away'],{'selector':8,'bgr555':0})
        self.assertEqual(result['teams'][4]['home'],{'selector':0,'bgr555':None})
        self.assertEqual(extract(bytes(512)+rom)['teams'],result['teams'])
        self.assertEqual(len(audit(rom,CAPTURE)['frames']),20)

    def test_changed_rom_rejected(self):
        rom=bytearray(ROM.read_bytes());rom[0x10459]^=1
        with self.assertRaises(ValueError):extract(bytes(rom))


if __name__=='__main__':unittest.main()
