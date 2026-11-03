import json
from pathlib import Path
import unittest
from audit_issd_descriptor_oam_bridge import audit

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
CAPTURE=ROOT/'analysis/bsnes-hair-long'
TRACE=ROOT/'docs/issd-match-trace-coverage.jsonl'


class DescriptorBridgeTest(unittest.TestCase):
    @unittest.skipUnless(ROM.exists() and (CAPTURE/'oam-audit.json').exists() and TRACE.exists(),'Requires local ROM and capture')
    def test_rom_rows_reconstruct_captured_body(self):
        result=audit(ROM.read_bytes(),CAPTURE,TRACE)
        self.assertEqual(len(result['frames']),76)
        self.assertEqual(len({f['descriptor'] for f in result['frames']}),10)
        self.assertTrue(all(f['pixels']>0 for f in result['frames']))
        self.assertEqual({f['reason'] for f in result['skipped']},{'geometry_or_bank_mismatch'})

    def test_rejects_invalid_rom(self):
        with self.assertRaises(ValueError):audit(bytes(0x8000),CAPTURE,TRACE)


if __name__=='__main__':unittest.main()
