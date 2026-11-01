import json
import unittest

from analyze_issd_native_dribble import analyze


class NativeDribbleTests(unittest.TestCase):
    def sample(self, **coordinates):
        return json.dumps({"frame": 2, "ball": {"x": 10, "y": 20, "z": 0},
                           "carrier": 0x500,
                           "actors": [{"address": 0x500, "x": 1000, "y": 2000,
                                       **coordinates}]})

    def test_legacy_projected_coordinates_are_not_comparable(self):
        report = analyze([self.sample()])
        self.assertEqual(report["samples_with_actors_but_without_world_coordinates"], 1)
        self.assertEqual(report["nearest_actor_distance_native_units_not_possession"]["count"], 0)

    def test_raw_coordinates_override_projected_coordinates(self):
        report = analyze([self.sample(world_x=13, world_y=24)])
        self.assertEqual(report["distance_ball_to_carrier_candidate_native_units"]["median"], 5)
        self.assertEqual(report["samples_with_carrier_actor_match"], 1)

    def test_nonfinite_raw_coordinates_are_excluded(self):
        report = analyze([self.sample(world_x=float('nan'), world_y=24)])
        self.assertEqual(report["samples_with_carrier_actor_match"], 0)

    def test_repeated_frame_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze([self.sample(), self.sample()])


if __name__ == '__main__':
    unittest.main()
