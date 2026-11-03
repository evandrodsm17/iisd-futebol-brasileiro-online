import unittest
from pathlib import Path
from export_issd_goalkeeper_locomotion import export

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
TRACE=ROOT/'docs/issd-natural-play-trace.jsonl'


class GoalkeeperLocomotionTest(unittest.TestCase):
    def test_rejects_wrong_rom(self):
        with self.assertRaises(ValueError):export(bytes(0x8000),TRACE)

    @unittest.skipUnless(ROM.exists() and TRACE.exists(),'Requires local ROM and trace')
    def test_observed_geometry_and_missing_frames(self):
        result=export(ROM.read_bytes(),TRACE)
        self.assertEqual(len(result['cycles']),8)
        self.assertEqual(sum(f is not None for c in result['cycles'] for f in c['frames']),61)
        self.assertEqual(len(result['missing']),3)
        self.assertTrue(all(item['direction']==4 for item in result['missing']))


if __name__=='__main__':unittest.main()
