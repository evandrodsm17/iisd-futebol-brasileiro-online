"""Tests for measured (not invented) ISSD action timing."""
from __future__ import annotations

import unittest

from report_issd_native_action_timing import audit, runs, summarize


def sample(frame, cursor, descriptor):
    return {"frame": frame, "actor": {
        "address": 0x0C00, "animation_script": 0xD007,
        "direction": 7, "animation_cursor": cursor, "descriptor": descriptor,
    }}


class NativeActionTimingTest(unittest.TestCase):
    def test_measured_intervals_and_lower_bound(self):
        timeline = [
            sample(100, 2, 0xA5E1), sample(102, 4, 0xA5EA),
            sample(103, 6, 0xA5F3), sample(104, 8, 0xA5FC),
            sample(105, 10, 0xA605), sample(106, 12, 0xA60E),
            sample(109, 12, 0xA60E),
        ]
        result = summarize(timeline)
        self.assertEqual(result["transition_intervals_frames"], [2, 1, 1, 1, 1])
        self.assertEqual(result["last_pose_minimum_observed_frames"], 4)
        self.assertFalse(result["exact_final_hold_known"])

    def test_separate_new_runs(self):
        data = [sample(100, 2, 0xA5E1), sample(102, 4, 0xA5EA),
                sample(300, 2, 0xA5E1), sample(302, 4, 0xA5EA)]
        self.assertEqual(len(runs(data)), 2)

    def test_median_and_unverified_final(self):
        data = [sample(100, 2, 0xA5E1), sample(102, 4, 0xA5EA),
                sample(103, 6, 0xA5F3), sample(106, 6, 0xA5F3)]
        group = audit(data)["groups"][0]
        self.assertEqual([t["measured_transition_frames"] for t in group["timing"]], [2, 1, None])
        self.assertEqual(group["timing"][-1]["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
