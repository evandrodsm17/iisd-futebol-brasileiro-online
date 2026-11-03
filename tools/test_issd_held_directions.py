import unittest
from unittest.mock import patch
from audit_issd_held_directions import audit_trial


class HeldDirectionsTests(unittest.TestCase):
    def test_unobserved_selector_is_not_treated_as_success(self):
        baseline={'baseline_matches_observed_fields':True,'p2_action_input_confirmed':True,
                  'p2_control_neutral_in_action_window':True,'before_compared':240}
        origin={'observations':[{'path':'held_direction_lookup','dpad_nibble':10,'controller_held':0xA40,
                  'matches_lookup':True,'step':1,'actor':0x1900,'output_a':5}]}
        field={'observations':[{'matches_rom_formula':True,'step':1,'actor':0x1900,
                                'direction':1,'field_86_after':0x8004}]}
        with patch('audit_issd_held_directions.compare',return_value=baseline), \
             patch('audit_issd_held_directions.origin',return_value=origin), \
             patch('audit_issd_held_directions.field86',return_value=field), \
             patch('audit_issd_held_directions.selection',side_effect=ValueError('No matching selection sequence for the controlled actor')):
            result=audit_trial('UpLeft',[],{'samples':{}},{},[],[],[],[],[])
        self.assertTrue(result['field_checks_pass'])
        self.assertFalse(result['matched_all_checks'])
        self.assertFalse(result['alternate_route_observed'])
        self.assertIsNone(result['script'])


if __name__=='__main__':unittest.main()
