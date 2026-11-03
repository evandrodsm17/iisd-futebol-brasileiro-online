import unittest
from analyze_issd_draw_trace import slots, summarize


class DrawTraceTests(unittest.TestCase):
    def test_stack_range_to_slots(self):
        self.assertEqual(slots(0x34f, 0x337), list(range(36, 42)))
        with self.assertRaises(ValueError): slots(0x34f, 0x33a)

    def test_does_not_pair_different_steps(self):
        rows=[{'type':'draw_entry','step':1,'frame':1,'object':0x1900,'stack':0x34f,'list_y':0x1d42},
              {'type':'draw_entry','step':2,'frame':2,'object':0x400,'stack':0x337,'list_y':0x1d44}]
        self.assertEqual(summarize(rows,0x1900)['entries'][0]['status'],'missing-next-entry')


if __name__=='__main__': unittest.main()
