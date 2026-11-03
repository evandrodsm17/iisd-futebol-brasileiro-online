import unittest
from analyze_issd_alternate_action import analyze,verify_rom,REQUIRED


class AlternateActionTests(unittest.TestCase):
    def test_checks_dispatch_rows(self):
        rom=bytearray(0x10000);rom[0xbeb8:0xbec0]=bytes.fromhex('cf96d496cf963000');rom[0xbec0:0xbec8]=bytes.fromhex('e596e596e5963000')
        self.assertEqual(verify_rom(rom),0)
        rom[0xbeb8]=0
        with self.assertRaises(ValueError):verify_rom(rom)

    def test_rejects_incomplete_event_sequence(self):
        rows=[{'type':'alternate_hook_registration','address':name,'success':True} for name in REQUIRED]
        rows += [{'type':'experiment_start','p2':0x1900,'step':1},
                 {'type':'session_end','reason':'experiment_window_complete'}]
        with self.assertRaises(ValueError):analyze(rows)


if __name__=='__main__':unittest.main()
