import unittest
from analyze_issd_input_origin import analyze


class InputOriginTests(unittest.TestCase):
    def test_lookup_and_controlled_actor_only(self):
        hooks=('83F151','83F19F','83F1B1','80DD34','80DD45','80E770','80E7B0','80F455','80DE35')
        rows=[{'type':'input_origin_hook_registration','address':h,'success':True} for h in hooks]
        rows += [{'type':'experiment_start','p2':0x1900},
                 {'type':'input_origin_execution','dp':0x1900,'step':1,'address':'80DE35','a':31},
                 {'type':'input_origin_execution','dp':0x1900,'step':1,'address':'83F1B1','a':4,'direction':5,'controller_held':64},
                 {'type':'session_end','reason':'experiment_window_complete'}]
        table=bytearray(64);table[31]=0x84
        self.assertTrue(analyze(rows,table)['observations'][0]['matches_lookup'])
        table[31]=5
        self.assertFalse(analyze(rows,table)['observations'][0]['matches_lookup'])


if __name__=='__main__':unittest.main()
