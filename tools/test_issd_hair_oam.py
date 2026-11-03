from pathlib import Path
import unittest
from analyze_issd_hair_oam import analyze

ROOT=Path(__file__).resolve().parent.parent/'analysis'/'bsnes-hair-oam-visible'


@unittest.skipUnless((ROOT/'hair-runtime.jsonl').exists(),'Requires private emulator capture')
class HairOamTest(unittest.TestCase):
    def test_combined_pixels_and_known_limit(self):
        result=analyze(ROOT)
        self.assertEqual(len(result['frames']),19)
        self.assertEqual(result['exact_nonempty'],2)
        self.assertTrue(all(frame['hair_only_mismatches']==0 for frame in result['frames']))
        self.assertTrue(any(frame['nonmatching_pixels']>0 for frame in result['frames']))


if __name__=='__main__':unittest.main()
