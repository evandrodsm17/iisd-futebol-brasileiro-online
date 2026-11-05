import json
import tempfile
import unittest
from pathlib import Path
from audit_issd_shot_capture_coverage import audit


class ShotCoverageTest(unittest.TestCase):
    def test_complete_incomplete_and_other_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('vram', 'oam', 'cgram', 'screen'):
                (root / name).write_bytes(b'x')
            row = {'actor': {'animation_script': 0xd007, 'direction': 2, 'descriptor': 9},
                   'vram': 'vram', 'oam_ppu': 'oam', 'cgram_ppu': 'cgram', 'screenshot': 'screen'}
            incomplete = {**row, 'vram': 'absent'}
            other = {**row, 'actor': {**row['actor'], 'animation_script': 0xd100}}
            (root / 'trial-graphics.jsonl').write_text('\n'.join(map(json.dumps, (row, incomplete, other))), encoding='utf-8')
            result = audit(root)
            self.assertEqual(result['poses'], [{'direction': 2, 'descriptor': 9, 'snapshots': 2, 'complete': 1}])
            self.assertEqual(result['invalid_rows'], 0)


if __name__ == '__main__':
    unittest.main()
