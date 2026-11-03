import hashlib
import json
import unittest
from pathlib import Path

from extract_issd_action_scripts import decode_timed
from extract_issd_catalog import EXPECTED_MD5


ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
EXPECTED={
  0xdb25:([2,2,32],[[0xb29b,0xb2a4,0xb2ad],[0xb2d1,0xb2da,0xb2e3],[0xb307,0xb310,0xb319],
      [0xb2d1,0xb2da,0xb2e3],[0xb29b,0xb2a4,0xb2ad],[0xb265,0xb26e,0xb277],
      [0xb22f,0xb238,0xb241],[0xb265,0xb26e,0xb277]]),
  0xdb5b:([5,5,5],[[0xb2b6,0xb2bf,0xb2c8],[0xb2ec,0xb2f5,0xb2fe],[0xb322,0xb32b,0xb334],
      [0xb2ec,0xb2f5,0xb2fe],[0xb2b6,0xb2bf,0xb2c8],[0xb280,0xb289,0xb292],
      [0xb24a,0xb253,0xb25c],[0xb280,0xb289,0xb292]])}


class ActionScriptsTest(unittest.TestCase):
    @unittest.skipUnless(ROM.exists(),'Local ROM required')
    def test_timed_tables_and_observed_replay(self):
        rom=ROM.read_bytes();self.assertEqual(hashlib.md5(rom).hexdigest(),EXPECTED_MD5)
        for root,(ticks,expected) in EXPECTED.items():
            directions,actual_ticks=decode_timed(rom,root)
            self.assertEqual(actual_ticks,ticks)
            self.assertEqual([d['descriptors'] for d in directions],expected)
        data=json.loads((ROOT/'docs/issd-slide-visual-replay.json').read_text(encoding='utf-8'))
        observed=[x['descriptor'] for x in data['timeline'] if x['script'] in (0xdb25,0xdb5b)]
        self.assertEqual(observed,EXPECTED[0xdb25][1][0]+EXPECTED[0xdb5b][1][0])
        counts=[x['samples'] for x in data['timeline'] if x['script'] in (0xdb25,0xdb5b)]
        self.assertEqual(counts,[2,2,11,5,5,5])
        self.assertLess(counts[2],EXPECTED[0xdb25][0][2])


if __name__=='__main__':unittest.main()
