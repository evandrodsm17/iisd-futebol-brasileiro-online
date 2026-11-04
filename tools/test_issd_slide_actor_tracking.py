"""The selected player may change while the original slide continues."""
import unittest
from export_issd_slide_lab import tracked_descriptor

class TrackingTest(unittest.TestCase):
    def test_keeps_tracking_original_after_selection_changes(self):
        sample={'selected_p1':0xe00,'actor':{'descriptor':0xb8d4},'actors':[{'address':0xe00,'descriptor':0xb8d4},{'address':0xf00,'descriptor':0xb32b}]}
        self.assertEqual(tracked_descriptor(sample,0xf00),0xb32b)
    def test_missing_or_duplicate_actor_is_rejected(self):
        with self.assertRaises(ValueError): tracked_descriptor({'actors':[]},0xf00)
        with self.assertRaises(ValueError): tracked_descriptor({'actors':[{'address':0xf00},{'address':0xf00}]},0xf00)

if __name__=='__main__': unittest.main()
