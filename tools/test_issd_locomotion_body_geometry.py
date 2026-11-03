import json
from pathlib import Path
import unittest
from extract_issd_locomotion_body_geometry import extract
from audit_issd_locomotion_body_geometry import audit

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
HAIR=ROOT/'dist/data/issd-hair-locomotion-geometry.json'
TRACE=ROOT/'docs/issd-match-trace-coverage.jsonl'
CAPTURE=ROOT/'analysis/bsnes-actor-oam-props'
BRIDGE=ROOT/'analysis/bsnes-hair-detail-selector/descriptor-bridge.json'


class LocomotionBodyGeometryTest(unittest.TestCase):
    def test_rejects_wrong_rom(self):
        with self.assertRaises(ValueError):extract(bytes(0x8000),{})

    @unittest.skipUnless(ROM.exists() and TRACE.exists() and (CAPTURE/'hair-runtime.jsonl').exists() and BRIDGE.exists(),'Requires local ROM and captures')
    def test_geometry_against_all_directions_and_live_wram(self):
        rom=ROM.read_bytes();geometry=extract(rom,json.loads(HAIR.read_text(encoding='utf8')))
        result=audit(rom,geometry,TRACE,CAPTURE,json.loads(BRIDGE.read_text(encoding='utf8')))
        self.assertEqual(len(geometry['poses']),90)
        self.assertEqual(len(result['trace_cycles']),144)
        self.assertEqual(result['wram_samples'],76)
        self.assertEqual({v['direction'] for v in result['trace_cycles']},set(range(8)))


if __name__=='__main__':unittest.main()
