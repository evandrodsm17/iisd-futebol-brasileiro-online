import unittest
from verify_issd_contact_destinations import verify, ASM


class ContactDestinationTests(unittest.TestCase):
    def test_assembly_and_mutation(self):
        if not ASM.exists(): self.skipTest('Disassembly unavailable')
        source=ASM.read_text(encoding='utf-8')
        self.assertEqual(verify(source),6)
        start=source.index('CODE_85F45F:')
        changed=source[:start]+source[start:].replace('JSL.l CODE_80E3CE','JSL.l CODE_80E3CF',1)
        with self.assertRaises(ValueError): verify(changed)


if __name__=='__main__': unittest.main()
