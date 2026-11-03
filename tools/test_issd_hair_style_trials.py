from pathlib import Path
import unittest
from summarize_issd_hair_style_trials import summarize

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
CASES=[(1,ROOT/'analysis'/'bsnes-hair-oam-clear'),(2,ROOT/'analysis'/'bsnes-hair-style2'),
       (13,ROOT/'analysis'/'bsnes-hair-style13')]


@unittest.skipUnless(ROM.exists() and all((path/'hair-runtime.jsonl').exists() for _,path in CASES),
                     'Requires local ROM and private emulator captures')
class HairStyleTrialsTest(unittest.TestCase):
    def test_all_cases_and_wrong_style(self):
        result=summarize(ROM.read_bytes(),CASES)
        self.assertEqual([item['direct_exact_frames'] for item in result['cases']],[13,13,13])
        self.assertTrue(all(item['unexplained_pixels']==0 for item in result['cases']))
        with self.assertRaises(ValueError):
            summarize(ROM.read_bytes(),[(1,CASES[0][1]),(3,CASES[1][1]),CASES[2]])


if __name__=='__main__':unittest.main()
