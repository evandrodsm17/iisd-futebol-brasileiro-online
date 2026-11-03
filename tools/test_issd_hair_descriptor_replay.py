import json
from pathlib import Path
import unittest
from audit_issd_hair_descriptor_replay import audit
from export_issd_hair_descriptor_tiles import export

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
BRIDGE=ROOT/'analysis/bsnes-hair-detail-selector/descriptor-bridge.json'


class HairDescriptorReplayTest(unittest.TestCase):
    @unittest.skipUnless(ROM.exists() and BRIDGE.exists() and all((ROOT/'analysis'/name/'hair-runtime.jsonl').exists() for name in ('bsnes-hair-detail-selector','bsnes-hair-long-style2','bsnes-hair-long-style13')),'Requires local ROM and isolated captures')
    def test_all_styles_and_cycles(self):
        rom=ROM.read_bytes();bridge=json.loads(BRIDGE.read_text(encoding='utf8'));reports=[]
        for style,name in ((1,'bsnes-hair-detail-selector'),(2,'bsnes-hair-long-style2'),(13,'bsnes-hair-long-style13')):
            report=audit(rom,ROOT/'analysis'/name,bridge,style);reports.append(report)
            self.assertEqual(len(report['frames']),76)
            self.assertEqual(len({f['descriptor'] for f in report['frames']}),10)
        tiles=export(rom,reports)
        self.assertEqual(set(tiles['styles']),{'1','2','13'})

    def test_rejects_wrong_rom(self):
        with self.assertRaises(ValueError):audit(bytes(0x8000),ROOT,{},1)


if __name__=='__main__':unittest.main()
