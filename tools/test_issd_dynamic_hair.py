import json
from pathlib import Path
import unittest
from audit_issd_dynamic_hair import audit

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
CAPTURE=ROOT/'analysis'/'bsnes-hair-anchor-draw'
SHEET=ROOT/'dist'/'assets'/'issd'/'oam-teams'/'02'/'home'/'walking-4.png'


@unittest.skipUnless(ROM.exists() and (CAPTURE/'hair-runtime.jsonl').exists() and SHEET.exists(),
                     'Requires local ROM, generated sheet and private capture')
class DynamicHairTest(unittest.TestCase):
    def test_exact_composition_and_explicit_exclusions(self):
        data=ROOT/'dist'/'data'
        anchors=json.loads((data/'issd-locomotion-anchors.json').read_text(encoding='utf8'))
        geometry=json.loads((data/'issd-hair-locomotion-geometry.json').read_text(encoding='utf8'))
        result=audit(ROM.read_bytes(),CAPTURE,anchors,geometry,SHEET)
        self.assertEqual([f['step'] for f in result['frames']],[13,14,15,16])
        self.assertEqual(len(result['skipped']),9)
        self.assertTrue(all(f['color_differences']==7 and f['geometry_differences']==0 for f in result['skipped']))


if __name__=='__main__':unittest.main()
