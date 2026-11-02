import unittest
from analyze_issd_auto_control import analyze


class ControlProbeTests(unittest.TestCase):
    def test_fraction_and_non_owner_link(self):
        def row(step,fraction):
            return {'step':step,'input':'Right','selected_p1':0x600,'link_a6':0x700,
                    'controls':[{'address':0x1aa0,'actor':0x500,'flags':0,'held':0x100}],
                    'actors':[{'address':0x500,'type':1,'x':0,'x_fraction':fraction,'y':0,'y_fraction':0}]}
        result=analyze([row(2,0),{'type':'candidate_trigger','step':3},row(4,1),row(8,2)])['by_input']['Right']
        self.assertEqual(result['consecutive_pairs'],1)
        self.assertEqual(result['position_changed_pairs'],1)
        self.assertEqual(result['changed_pairs_with_other_link'],1)
        self.assertEqual(result['link_a6_other_actor'],3)
        self.assertEqual(result['pointer_differs_from_1acc'],3)

    def test_out_of_order(self):
        row={'step':2,'input':'Right'}
        with self.assertRaises(ValueError): analyze([row,row])


if __name__=='__main__': unittest.main()
