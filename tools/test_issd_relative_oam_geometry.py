import json
from pathlib import Path
import unittest
from audit_issd_relative_oam_geometry import audit

ROOT=Path(__file__).resolve().parent.parent
CAPTURE=ROOT/'analysis/bsnes-hair-detail-selector'
TRACE=ROOT/'docs/issd-match-trace-coverage.jsonl'
HAIR=ROOT/'dist/data/issd-dynamic-hair-anchor-audit.json'


class RelativeOamGeometryTest(unittest.TestCase):
    @unittest.skipUnless((CAPTURE/'descriptor-bridge.json').exists() and TRACE.exists(),'Requires local isolated capture')
    def test_observed_relative_geometry_matches_oam(self):
        result=audit(CAPTURE,TRACE,json.loads(HAIR.read_text(encoding='utf8')))
        self.assertEqual(len(result['frames']),76)
        self.assertEqual(len({f['descriptor'] for f in result['frames']}),10)
        self.assertEqual({f['attribute_xor'] for f in result['frames']},{0x13})


if __name__=='__main__':unittest.main()
