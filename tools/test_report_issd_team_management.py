import unittest
from report_issd_team_management import analyze
def row(frame,first="000102030405060708090A0B0C0D0E0F10111213"):
    return dict(frame=frame,phase=3,lineup_first=first,
        lineup_second="000102030405060708090A0B0C0D0E0F10111213",
        original_snapshot_first="000102030405060708090A0B0C0D0E0F10111213",
        original_snapshot_second="000102030405060708090A0B0C0D0E0F10111213",
        selector_first=65535,selector_second=65535,
        team_record_a6_first=0,team_record_a6_second=0,
        selected_actor_candidate=1536,p1_raw_0010=0,p1_held_0020=0,p1_pressed_0028=0)
class TestObservation(unittest.TestCase):
    def test_one_slot_changed_not_named_substitution(self):
        changed="000C02030405060708090A0B0C0D0E0F10111213"
        result=analyze([row(1),row(2,changed)])
        self.assertEqual(result["changes"],1)
        self.assertEqual(result["events"][0]["changed"]["lineup_first"],[dict(slot=1,**{"from":1,"to":12})])
        self.assertNotIn("substitution",str(result["events"]).lower())
    def test_unchanged(self):self.assertEqual(analyze([row(1),row(2)])["changes"],0)
    def test_reject_duplicate_frames(self):
        with self.assertRaises(ValueError):analyze([row(1),row(1)])
if __name__=="__main__":unittest.main()
