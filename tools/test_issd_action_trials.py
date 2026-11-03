import copy
import unittest
from compare_issd_action_trials import compare


def row(x):
    return {'mode1':6,'mode2':8,'phase':0,'player_setting':4,'selected_p1':0x500,
            'link_a4':0,'link_a6':0,'ball':{'x':x,'y':0,'z':0},'actors':[],'controls':[]}


class ActionTrialsTests(unittest.TestCase):
    def test_matching_and_diverging(self):
        first={'samples':{**{i:row(0) for i in range(0,480,2)},480:row(0)}}
        second=copy.deepcopy(first);second['samples'][480]['ball']['x']=1
        result=compare(first,second)
        self.assertTrue(result['baseline_matches_observed_fields'])
        self.assertEqual(result['first_after_ball_difference'],480)
        second['samples'][2]['ball']['x']=1
        self.assertFalse(compare(first,second)['baseline_matches_observed_fields'])

    def test_empty_baseline_is_not_valid(self):
        self.assertFalse(compare({'samples':{}},{'samples':{}})['baseline_matches_observed_fields'])

    def test_a_bit_does_not_make_other_button_neutral(self):
        first={'samples':{i:row(0) for i in range(0,486,2)}}
        second=copy.deepcopy(first)
        for i in (480,482,484):
            first['samples'][i]['held_p2']=0x80
            second['samples'][i]['held_p2']=0x8000
        result=compare(first,second)
        self.assertTrue(result['p2_action_input_confirmed'])
        self.assertFalse(result['p2_control_neutral_in_action_window'])

    def test_explicit_action_mask(self):
        first={'samples':{i:row(0) for i in range(0,486,2)}}
        second=copy.deepcopy(first)
        for i in (480,482,484): first['samples'][i]['held_p2']=0x40
        self.assertTrue(compare(first,second,0x40)['p2_action_input_confirmed'])
        self.assertFalse(compare(first,second)['p2_action_input_confirmed'])

    def test_ball_record_detects_type_without_position_change(self):
        first={'samples':{480:row(0)}}
        second=copy.deepcopy(first)
        first['samples'][480]['ball']['type']=23
        second['samples'][480]['ball']['type']=30
        result=compare(first,second)
        self.assertEqual(result['after_ball_difference_count'],0)
        self.assertEqual(result['after_ball_record_difference_count'],1)

    def test_extra_samples_do_not_invalidate_complete_baseline(self):
        first={'samples':{i:row(0) for i in range(486)}}
        second=copy.deepcopy(first)
        for i in range(480,486):first['samples'][i]['held_p2']=0x80
        result=compare(first,second)
        self.assertTrue(result['baseline_matches_observed_fields'])
        self.assertTrue(result['p2_action_input_confirmed'])
        self.assertTrue(result['p2_control_neutral_in_action_window'])

    def test_many_samples_without_complete_parity_are_rejected(self):
        first={'samples':{i:row(0) for i in range(480) if i not in (0,1)}}
        result=compare(first,copy.deepcopy(first))
        self.assertGreaterEqual(result['before_compared'],240)
        self.assertFalse(result['baseline_matches_observed_fields'])


if __name__=='__main__': unittest.main()
