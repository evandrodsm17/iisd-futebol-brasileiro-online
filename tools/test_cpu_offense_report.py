import unittest
from report_issd_cpu_offense import analyze


class OffenseReportTests(unittest.TestCase):
    def report(self, **coordinates):
        return analyze([{"frame": 1, "carrier_candidate": 0x5588,
                         "ball": {"x": 10, "y": 20, "z": 0},
                         "actors": [{"address": 0x500, "script": 0xD007,
                                     "x": 1000, "y": 2000, **coordinates}]}])

    def test_legacy_coordinates_and_ownership_are_not_inferred(self):
        event = self.report()["events"][0]
        self.assertIsNone(event["proximity"])
        self.assertNotIn("carrier_matches_actor", event)
        self.assertEqual(event["object_1b90_word"], 0x5588)

    def test_raw_coordinate_distance(self):
        event = self.report(world_x=13, world_y=24)["events"][0]
        self.assertEqual(event["proximity"], 5)

    def test_nonfinite_coordinate_is_excluded(self):
        event = self.report(world_x=float('inf'), world_y=24)["events"][0]
        self.assertIsNone(event["proximity"])


if __name__ == '__main__':
    unittest.main()
