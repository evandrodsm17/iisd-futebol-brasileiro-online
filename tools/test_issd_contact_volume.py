import unittest
from issd_contact_volume import axis_carry, contact_volume, extract, ASM, ROOT


class ContactVolumeTests(unittest.TestCase):
    def test_three_axis_order_and_flags(self):
        words=[16,32,16,32,16,32]
        def check(ball,**kw):
            return contact_volume(words,(0,0,0),(0,0,0),ball,
                phase=kw.get('phase',0),flag_11fa=kw.get('flag_11fa',0),
                actor_flags=kw.get('actor_flags',0))
        self.assertEqual(check((0,0,0)),{'carry':0,'actor_flags':0x400,'rejected_by':None})
        self.assertEqual(check((0,0,100))['rejected_by'],'z')
        self.assertEqual(check((100,0,0))['rejected_by'],'x')
        self.assertEqual(check((0,100,0))['rejected_by'],'y')
        self.assertEqual(check((0,0,0),phase=1)['rejected_by'],'gate')
        self.assertEqual(check((0,0,0),flag_11fa=0x8000)['rejected_by'],'gate')
        self.assertEqual(check((0,0,0),actor_flags=0x400)['rejected_by'],'gate')

    def test_input_validation(self):
        with self.assertRaises(ValueError):
            contact_volume([0]*6,(0,0,-1),(0,0,0),(0,0,0),phase=0,flag_11fa=0,actor_flags=0)

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
