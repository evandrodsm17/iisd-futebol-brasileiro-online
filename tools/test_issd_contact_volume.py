import unittest
from issd_contact_volume import axis_carry, extract, ASM, ROOT


class ContactVolumeTests(unittest.TestCase):
    def test_second_adc_carry_changes_first_sbc(self):
        self.assertEqual(axis_carry(0,0,0,0,0),1)
        self.assertEqual(axis_carry(0xffff,0,1,0,0),1)
        self.assertEqual(axis_carry(1,0,0,0,1),0)
        self.assertEqual(axis_carry(2,0,0,0,1),1)

    def test_local_rom_and_mismatch(self):
        path=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
        if not path.exists() or not ASM.exists(): self.skipTest('Local ROM/disassembly unavailable')
        source=ASM.read_text(encoding='utf-8'); rom=path.read_bytes()
        result=extract(source,rom)
        self.assertEqual(result['tables'][0]['words'],[16,32,16,32,16,32])
        self.assertEqual(result['tables'][1]['words'],[16,32,16,32,28,56])
        header=len(rom)%0x8000
        changed=bytearray(rom); changed[header+0xcf5f]^=1
        with self.assertRaises(ValueError): extract(source,bytes(changed))
        self.assertEqual(extract(source,bytes(512)+rom[header:])['tables'],result['tables'])


if __name__=='__main__': unittest.main()
