"""Regression tests for action sprite evidence audit."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from report_issd_action_sprite_gaps import (
    aggregate_reports, build_report, collect_captures, collect_runtime,
    lowkick_assets,
)


class ActionSpriteGapsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.static = {"actions": {"test_action": {
            "script": "$82:D100", "directions": [
                {"direction": 0, "descriptors": [0xABF6, 0xAC50, 0xAC50]},
                {"direction": 1, "descriptors": [0xABF6, 0xAC50]},
            ],
        }}}

    def file(self, name, payload):
        p = self.root / name
        p.write_text(json.dumps(payload), encoding="utf-8")
        return p

    def test_aggregate_does_not_claim_directional_evidence(self):
        summary = self.file("summary.json", {"scripts": [{"script": "$D100", "descriptors": {"$ABF6": 2}}]})
        report = build_report(self.static, aggregate_reports([summary]), {}, {}, {}, [], {}, False, False)
        action = report["actions"][0]
        self.assertEqual(action["aggregate_observed_descriptors_all_directions"], ["$ABF6"])
        self.assertIsNone(action["directions"][0]["runtime_observed"])
        self.assertIsNone(action["directions"][1]["runtime_observed"])
        self.assertEqual(action["directions"][0]["static_entries_including_repeats"], 3)

    def test_raw_runtime_is_direction_specific(self):
        trace = self.root / "match.jsonl"
        trace.write_text(json.dumps({"frame": 10, "actors": [
            {"animation_script": 0xD100, "direction": 0, "descriptor": 0xABF6},
        ]}) + "\n", encoding="utf-8")
        runtime = collect_runtime([trace])
        report = build_report(self.static, {}, runtime, {}, {}, [], {}, True, False)
        d0, d1 = report["actions"][0]["directions"]
        self.assertEqual(d0["runtime_observed"], ["$ABF6"])
        self.assertEqual(d0["runtime_missing_candidates"], ["$AC50"])
        self.assertEqual(d1["runtime_observed"], [])
        self.assertEqual(d1["runtime_missing_candidates"], ["$ABF6", "$AC50"])

    def test_same_frame_capture_needs_real_files(self):
        vram = self.root / "same.bin"
        cgram = self.root / "same.hex"
        vram.write_bytes(bytes(65536))
        cgram.write_text("00" * 512, encoding="utf-8")
        capture = self.root / "action.jsonl"
        capture.write_text("\n".join(json.dumps({
            "frame": i, "obsel": 0, "vram": vram.name,
            "cgram": cgram.name if i == 1 else "missing.hex",
            "actor": {"animation_script": 0xD100, "direction": 0,
                      "descriptor": 0xABF6 if i == 1 else 0xAC50,
                      "parts": [{"x": 0, "y": 0, "tile": 1, "size": 16, "attr": 0}]},
        }) for i in (1, 2)) + "\n", encoding="utf-8")
        observations, renderable, invalid = collect_captures([capture])
        self.assertEqual(set(observations[0xD100][0]), {0xABF6, 0xAC50})
        self.assertEqual(set(renderable[0xD100][0]), {0xABF6})
        self.assertEqual(len(invalid), 1)

    def test_lowkick_is_asset_evidence_not_action_label(self):
        mapping = self.file("assets.json", {"scripts": [{"script": "$D100", "frames": [
            {"descriptor": "$ABF6", "asset": "GFX_Sprite_Player_DiagonalUp_LowKick1", "samples": 2},
            {"descriptor": "$AC50", "asset": "GFX_Sprite_Player_Side_Running1", "samples": 2},
        ]}]})
        matches = lowkick_assets(mapping)
        self.assertEqual(len(matches[0xD100]), 1)
        self.assertEqual(matches[0xD100][0]["descriptor"], "$ABF6")


if __name__ == "__main__":
    unittest.main()
