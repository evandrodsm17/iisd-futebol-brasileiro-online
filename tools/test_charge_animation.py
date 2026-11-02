import unittest
from extract_issd_charge_animation import extract,ASM,ROOT


class ChargeAnimationTests(unittest.TestCase):
    def test_tables_header_and_mutation(self):
        path=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
        if not path.exists() or not ASM.exists(): self.skipTest('Local ROM/disassembly unavailable')
        source=ASM.read_text(encoding='utf-8');rom=path.read_bytes()
        result=extract(source,rom)
        self.assertEqual(result['tables']['82CFAF']['values'],[4,3,3,3,4,3,3,3])
        self.assertEqual(result['tables']['82CFB7']['values'][-1],0x26f8)
        header=len(rom)%0x8000
        self.assertEqual(extract(source,bytes(512)+rom[header:])['tables'],result['tables'])
        changed=bytearray(rom);changed[header+0x14faf]^=1
        with self.assertRaises(ValueError): extract(source,bytes(changed))


if __name__=='__main__': unittest.main()
