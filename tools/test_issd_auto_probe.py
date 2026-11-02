import unittest
from analyze_issd_auto_probe import analyze


class AutoProbeTests(unittest.TestCase):
    def test_complete_and_valid_samples(self):
        rows=[{'type':'session_start','target_frames':2},
              {'step':2,'input':'Right','held_p1':256,'actor_slot_valid':True,'player_setting':0},
              {'type':'session_end','steps':2}]
        result=analyze(rows)
        self.assertTrue(result['complete']);self.assertEqual(result['valid_actor_samples_by_input'],{'Right':1})
        self.assertEqual(result['held_words_by_input'][0]['held'],256)

    def test_incomplete_and_repeated_step(self):
        row={'step':2,'input':'A','held_p1':0,'actor_slot_valid':False}
        self.assertFalse(analyze([row])['complete'])
        with self.assertRaises(ValueError): analyze([row,row])


if __name__=='__main__': unittest.main()
