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

    @unittest.skipUnless(all((ROOT/'analysis'/f'bsnes-hair-long-style{s}'/'hair-runtime.jsonl').exists() for s in (2,13)), 'Requires synthetic style captures')
    def test_additional_styles_against_same_frame_oam(self):
        data=ROOT/'dist'/'data'
        anchors=json.loads((data/'issd-locomotion-anchors.json').read_text(encoding='utf8'))
        geometry=json.loads((data/'issd-hair-locomotion-geometry.json').read_text(encoding='utf8'))
        baseline=json.loads((data/'issd-dynamic-hair-anchor-audit.json').read_text(encoding='utf8'))
        keys=('step','descriptor','sheet_frame','origin_x','origin_y','hair_x','hair_y','selector','detail')
        for style in (2,13):
            result=audit(ROM.read_bytes(),ROOT/'analysis'/f'bsnes-hair-long-style{style}',anchors,geometry,SHEET)
            self.assertEqual(result['style'],style)
            self.assertEqual(len(result['frames']),76)
            self.assertEqual({f['sheet_frame'] for f in result['frames']},set(range(10)))
            self.assertEqual(result['palette_rgb'],baseline['palette_rgb'])
            self.assertEqual([{k:f[k] for k in keys} for f in result['frames']],
                             [{k:f[k] for k in keys} for f in baseline['frames']])


if __name__=='__main__':unittest.main()
