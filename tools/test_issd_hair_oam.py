from pathlib import Path
import unittest
from analyze_issd_hair_oam import analyze

ROOT=Path(__file__).resolve().parent.parent/'analysis'/'bsnes-hair-oam-visible'
CLEAR=ROOT.parent/'bsnes-hair-oam-clear'


@unittest.skipUnless((ROOT/'hair-runtime.jsonl').exists(),'Requires private emulator capture')
class HairOamTest(unittest.TestCase):
    def test_combined_pixels_and_known_limit(self):
        result=analyze(ROOT)
        self.assertEqual(len(result['frames']),19)
        self.assertEqual(result['exact_nonempty'],2)
        self.assertTrue(all(frame['hair_only_mismatches']==0 for frame in result['frames']))
        self.assertTrue(any(frame['nonmatching_pixels']>0 for frame in result['frames']))

    @unittest.skipUnless((CLEAR/'hair-runtime.jsonl').exists(),'Requires separate isolated capture')
    def test_clear_capture_occlusion_audit(self):
        result=analyze(CLEAR)
        self.assertEqual((len(result['frames']),result['exact_nonempty']),(19,13))
        self.assertEqual(sum(f['earlier_slot_rgb_matches'] for f in result['frames']),71)
        self.assertEqual(sum(f['unexplained_after_earlier_slots'] for f in result['frames']),0)


if __name__=='__main__':unittest.main()
