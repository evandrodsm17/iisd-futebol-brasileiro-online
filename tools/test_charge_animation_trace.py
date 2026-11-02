import json
import unittest
from analyze_charge_animation_trace import analyze


class ChargeTraceTests(unittest.TestCase):
    def test_consecutive_samples_and_filtering(self):
        def row(frame,state,script):
            return json.dumps({'frame':frame,'actors':[{'address':1280,'state':state,
                'animation_script':script,'descriptor':0xa749,'direction':0}]})
        result=analyze([row(2,0x430,0xcf9f),row(4,0x438,0xcf9f),row(8,0x440,0xcf9f)])
        self.assertEqual(result['state_samples'],{'0430':1,'0438':1,'0440':1})
        self.assertEqual(result['cf9f_descriptors_in_target_states'],{'A749':3})
        self.assertEqual(result['sampled_state_transitions'],[{'from':'0430','to':'0438','count':1}])

    def test_nonmonotonic_rejected(self):
        row=json.dumps({'frame':2,'actors':[]})
        with self.assertRaises(ValueError): analyze([row,row])


if __name__=='__main__': unittest.main()
