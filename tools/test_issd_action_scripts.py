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
KICK={0xd007:[0xa617,0xa64d,0xa683,0xa64d,0xa617,0xa5e1,0xa5ab,0xa5e1],
      0xd100:[0xac23,0xac59,0xac8f,0xac59,0xac23,0xabed,0xabb7,0xabed]}
TURN=[0xab66,0xab81,0xab9c,0xab81,0xab66,0xab4b,0xab30,0xab4b]


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
        recovery,alternate=decode_timed(rom,0xdb5b,0xdb6f)
        self.assertEqual(alternate,[16,16,16])
        self.assertEqual([d['descriptors'] for d in recovery],EXPECTED[0xdb5b][1])
        longer=json.loads((ROOT/'docs/issd-defense-recovery.json').read_text(encoding='utf-8'))
        recovered=[x for x in longer['action_segments'] if x['state']==0x2f8 and x['script']==0xdb5b]
        self.assertEqual([x['descriptor'] for x in recovered],EXPECTED[0xdb5b][1][0])
        self.assertEqual([x['frames'] for x in recovered],alternate)

    @unittest.skipUnless(ROM.exists(),'Local ROM required')
    def test_shared_kick_and_turn_timing_tables(self):
        rom=ROM.read_bytes();self.assertEqual(hashlib.md5(rom).hexdigest(),EXPECTED_MD5)
        for root,starts in KICK.items():
            directions,ticks=decode_timed(rom,root,0xd017)
            self.assertEqual(ticks,[6,1,1,1,1,24,4])
            self.assertEqual([d['descriptors'] for d in directions],
                             [[start+9*i for i in range(6)]+[start+36] for start in starts])
        variants=[[5,5,5],[5,4,4],[4,4,4],[4,3,3],[3,3,3]]
        for i,expected in enumerate(variants):
            directions,ticks=decode_timed(rom,0xd79b,0xd7ab+4*i)
            self.assertEqual(ticks,expected)
            self.assertEqual([d['descriptors'] for d in directions],
                             [[start,start+9,start+18] for start in TURN])


if __name__=='__main__':unittest.main()
