import json
from pathlib import Path
import unittest
from audit_issd_uniform_detail_replay import audit

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
CAPTURE=ROOT/'analysis/bsnes-hair-detail-selector'


class UniformDetailReplayTest(unittest.TestCase):
    @unittest.skipUnless(ROM.exists() and (CAPTURE/'descriptor-bridge.json').exists(),'Requires local ROM and isolated capture')
    def test_rom_selection_matches_every_captured_tile(self):
        bridge=json.loads((CAPTURE/'descriptor-bridge.json').read_text(encoding='utf8'))
        report=audit(ROM.read_bytes(),CAPTURE,bridge)
        self.assertEqual(len(report['frames']),76)
        self.assertEqual(len({f['descriptor'] for f in report['frames']}),10)
        self.assertEqual({f['detail_source'] for f in report['frames']},{None,'$EFF4'})
        self.assertTrue(all(f['actor']=={'type':4,'kit_variant':14,'uniform_selector':4,'object_flags':64} for f in report['frames']))

    def test_rejects_wrong_rom(self):
        with self.assertRaises(ValueError):audit(bytes(0x8000),CAPTURE,{})


if __name__=='__main__':unittest.main()
