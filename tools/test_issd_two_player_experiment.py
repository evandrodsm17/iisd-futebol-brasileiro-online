import unittest
from analyze_issd_two_player_experiment import analyze


class ExperimentTests(unittest.TestCase):
    def test_windows_and_actor_fraction(self):
        def row(step,fraction):
            return {'step':step,'ball':{'x':0,'y':0,'z':0},
                    'controls':[{'address':0x1aa0,'actor':0x500,'held':0x100}],
                    'actors':[{'address':0x500,'type':1,'x':0,'x_fraction':fraction,'y':0,'y_fraction':0}]}
        result=analyze([{'type':'experiment_start','step':100},row(160,0),row(162,1),
                        {'type':'session_end','steps':200}])
        self.assertEqual(result['actors']['p1_right_p1']['changed'],1)
        self.assertEqual(result['samples_by_window']['p1_right'],2)

    def test_untriggered(self):
        self.assertIsNone(analyze([{'type':'session_end'}])['trigger_step'])


if __name__=='__main__': unittest.main()
