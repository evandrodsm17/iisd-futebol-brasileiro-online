import unittest
from verify_issd_action_charge_route import verify,ASM,ROOT


class ChargeRouteTests(unittest.TestCase):
    def test_rom_and_mutation(self):
        rom_path=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
        if not rom_path.exists() or not ASM.exists(): self.skipTest('Local ROM/disassembly unavailable')
        source=ASM.read_text(encoding='utf-8');rom=rom_path.read_bytes()
        self.assertEqual(verify(source,rom),4)
        header=len(rom)%0x8000
        changed=bytearray(rom);changed[header+0xc188]^=1
        with self.assertRaises(ValueError): verify(source,bytes(changed))
        self.assertEqual(verify(source,bytes(512)+rom[header:]),4)


if __name__=='__main__': unittest.main()
