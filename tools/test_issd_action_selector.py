import unittest
from analyze_issd_action_selector import analyze,rom_tables


class SelectorTests(unittest.TestCase):
    def rows(self):
        rows=[{'type':'selection_hook_registration','success':True,'address':address}
              for address in ('84968B','80E4C7','84E600','84E60C')]
        rows += [{'type':'experiment_start','p2':0x1900},
                 {'type':'selection_execution','address':'84968B','step':1,'dp':0x1900},
                 {'type':'selection_execution','address':'80E4C7','step':1,'dp':0x1900},
                 {'type':'selection_execution','address':'84E600','step':1,'frame':1,'dp':0x1900,
                  'field_86':0x0481,'direction':5,'x':4,'a':0xd169,'y':0xd16e},
                 {'type':'session_end','reason':'experiment_window_complete'}]
        return rows

    def test_verifies_observed_table_selection(self):
        r=analyze(self.rows(),[0,0,0xd169,0],[0,0,0xd16e,0])
        self.assertTrue(r['observations'][0]['matches_rom_table'])
        self.assertFalse(analyze(self.rows(),[0,0,0xd169,0],[0,0,0xd1c5,0])['observations'][0]['matches_rom_table'])

    def test_rejects_invalid_rom(self):
        with self.assertRaises(ValueError):rom_tables(bytes(3))


if __name__=='__main__':unittest.main()
