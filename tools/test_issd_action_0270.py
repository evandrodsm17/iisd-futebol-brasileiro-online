import unittest
from verify_issd_action_0270 import verify,ASM
from extract_issd_ball_attachment import ROOT


class Action0270Tests(unittest.TestCase):
    def test_rom_and_mutations(self):
        p=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
        if not p.exists() or not ASM.exists():self.skipTest('Local ROM/disassembly unavailable')
        source=ASM.read_text(encoding='utf-8');rom=p.read_bytes();header=len(rom)%0x8000
        self.assertEqual(verify(source,rom),3)
        changed=bytearray(rom);changed[header+0xbfc8]^=1
        with self.assertRaises(ValueError):verify(source,bytes(changed))
        self.assertEqual(verify(source,bytes(512)+rom[header:]),3)


if __name__=='__main__':unittest.main()
