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
        self.assertEqual([f['step'] for f in result['frames']],list(range(13,26)))
        self.assertEqual(len(result['skipped']),0)
        self.assertEqual(sum(f['detail'] is not None for f in result['frames']),9)
        self.assertTrue(all(f['detail']['palette']==5 for f in result['frames'] if f['detail']))

    @unittest.skipUnless((ROOT/'analysis'/'bsnes-hair-long'/'hair-runtime.jsonl').exists(), 'Requires extended local capture')
    def test_extended_capture_covers_full_cycle_consistently(self):
        data=ROOT/'dist'/'data'
        result=audit(ROM.read_bytes(),ROOT/'analysis'/'bsnes-hair-long',
                     json.loads((data/'issd-locomotion-anchors.json').read_text(encoding='utf8')),
                     json.loads((data/'issd-hair-locomotion-geometry.json').read_text(encoding='utf8')),SHEET)
        self.assertEqual({f['sheet_frame'] for f in result['frames']},set(range(10)))
        self.assertEqual(len(result['frames']),76)
        for frame in range(10):
            values=[{k:v for k,v in f.items() if k not in ('step','body_pixels','hair_pixels')}
                    for f in result['frames'] if f['sheet_frame']==frame]
            self.assertTrue(all(v==values[0] for v in values))


if __name__=='__main__':unittest.main()
