import json
from pathlib import Path
import unittest
from analyze_issd_hair_vram import analyze

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
TRACE=ROOT/'analysis'/'bsnes-hair-vram'/'hair-runtime.jsonl'


@unittest.skipUnless(ROM.exists() and TRACE.exists(),'Requires local ROM and private emulator trace')
class HairVramTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM.read_bytes()
        cls.rows=[json.loads(line) for line in TRACE.read_text(encoding='utf8').splitlines()]

    def test_runtime_atlas_matches(self):
        result=analyze(self.rom,self.rows)
        self.assertEqual(result['counts']['same_step_match'],81)
        self.assertEqual(result['counts']['next_frame_stable_match'],78)

    def test_stable_corruption_and_missing_hook_fail(self):
        rows=[dict(r) for r in self.rows]
        row=next(r for r in rows if r.get('type')=='vram' and r['step']==6)
        row['bytes']='ff'*32
        with self.assertRaises(ValueError):analyze(self.rom,rows)
        with self.assertRaises(ValueError):analyze(self.rom,[r for r in self.rows if r.get('type')!='hook'])


if __name__=='__main__':unittest.main()
