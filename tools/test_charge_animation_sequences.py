import json
import unittest
from report_charge_animation_sequences import analyze


class SequenceTests(unittest.TestCase):
    def test_gap_and_absent_actor_split_runs(self):
        def row(frame,actors): return json.dumps({'frame':frame,'actors':actors})
        a={'address':1280,'state':0x438,'animation_script':0xcf9f}
        runs=analyze([row(2,[a]),row(4,[a]),row(8,[a]),row(10,[]),row(12,[a])])
        self.assertEqual([len(run['samples']) for run in runs],[2,1,1])

    def test_out_of_order_rejected(self):
        row=json.dumps({'frame':2,'actors':[]})
        with self.assertRaises(ValueError): analyze([row,row])


if __name__=='__main__': unittest.main()
