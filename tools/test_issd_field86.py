import unittest
from analyze_issd_field86 import evaluate,read_table,EXPECTED_ROUTINE


class Field86Tests(unittest.TestCase):
    def test_direction_wraps_modulo_eight(self):
        table=[0,0x281,0x282,0x283,0x8004,0x483,0x482,0x481]
        entry={'step':1,'dp':0x1900,'a':4,'field_84':4,'direction':5,'field_86':0}
        result={'step':1,'dp':0x1900,'direction':5,'field_86':0x481,'a':0x481,'y':14}
        observation=evaluate(entry,result,table)
        self.assertEqual(observation['difference_mod_8'],7)
        self.assertTrue(observation['matches_rom_formula'])
        result['field_86']=0
        self.assertFalse(evaluate(entry,result,table)['matches_rom_formula'])

    def test_checks_exact_rom_routine(self):
        rom=bytearray(0x10000);rom[0x648d:0x649b]=EXPECTED_ROUTINE
        self.assertEqual(read_table(rom),[0]*8)
        rom[0x648d]=0
        with self.assertRaises(ValueError):read_table(rom)


if __name__=='__main__':unittest.main()
