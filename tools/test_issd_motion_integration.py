"""Integration checks using synthetic buffers, never the user's ROM."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASM = ROOT / 'YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm'
SCRIPT = ROOT / 'tools/extract_issd_motion_integration.py'
TABLE = bytes.fromhex('0007400240078002c007c0020008800280078002800740020007c0028008c002')


@unittest.skipUnless(ASM.exists(), 'local disassembly required')
class VerificationTests(unittest.TestCase):
    def run_case(self, header=0, corrupt=False, malformed=False):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rom = bytearray(0x10000)
            rom[0xEC47:0xEC67] = TABLE
            if corrupt:
                rom[0xEC47] ^= 1
            rom = bytes(header) + rom
            if malformed:
                rom += b'!'
            input_path, output_path = root / 'synthetic.sfc', root / 'result.json'
            input_path.write_bytes(rom)
            result = subprocess.run([sys.executable, str(SCRIPT), str(ASM), str(output_path), '--rom', str(input_path)], capture_output=True, text=True)
            self.assertEqual(input_path.read_bytes(), rom)
            if corrupt or malformed:
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output_path.exists())
                self.assertIn('differs from disassembly' if corrupt else 'unsupported ROM size', result.stderr)
            else:
                self.assertEqual(result.returncode, 0, result.stderr)
                data = json.loads(output_path.read_text())
                proof = data['limit_provenance']['rom_verification']
                self.assertEqual(proof['status'], 'byte_exact')
                self.assertEqual(proof['copier_header_bytes'], header)
                self.assertEqual(len(data['limit_provenance']['cases']), 8)

    def test_unheadered(self):
        self.run_case()

    def test_copier_header(self):
        self.run_case(header=512)

    def test_table_mismatch(self):
        self.run_case(corrupt=True)

    def test_invalid_length(self):
        self.run_case(malformed=True)


if __name__ == '__main__':
    unittest.main()
