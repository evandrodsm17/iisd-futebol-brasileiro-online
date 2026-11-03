import unittest
import json
import tempfile
from pathlib import Path
from analyze_issd_graphics_replay import compare_oam, report


class GraphicsReplayTests(unittest.TestCase):
    def test_normalizes_reverse_low_table_only(self):
        raw = bytes(range(256)) * 2 + bytes(range(32))
        hardware = raw[:512][::-1] + raw[512:]
        self.assertEqual(compare_oam(raw, hardware), 0)
        changed = bytearray(hardware)
        changed[512] ^= 1
        self.assertEqual(compare_oam(raw, changed), 1)

    def test_rejects_truncated_oam(self):
        with self.assertRaises(ValueError): compare_oam(b'', bytes(544))

    def test_detects_one_frame_offset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = []
            for frame in range(3):
                mirror = bytes([frame + 1]) * 544
                ppu = bytes([frame]) * 544
                (root / f'm{frame}').write_bytes(mirror)
                (root / f'p{frame}').write_bytes(ppu)
                (root / f'v{frame}').write_bytes(bytes(65536))
                (root / f'c{frame}').write_text(bytes([frame + 1] * 512).hex())
                (root / f'pc{frame}').write_bytes(bytes([frame] * 512))
                rows.append({'schema': 'issd-native-action-oam/v1', 'frame': frame,
                             'oam_mirror': f'm{frame}', 'oam_ppu': f'p{frame}',
                             'vram': f'v{frame}', 'cgram': f'c{frame}', 'cgram_ppu': f'pc{frame}',
                             'actor': {'address': 1, 'animation_script': 2, 'descriptor': 3,
                                       'direction': 0, 'pose': 4}})
            trace = root / 'trace.jsonl'
            trace.write_text(''.join(json.dumps(r) + '\n' for r in rows))
            result = report(trace)
            for key in ('oam_frame_offsets', 'cgram_frame_offsets'):
                offset = next(r for r in result[key] if r['ppu_frame_offset'] == 1)
                self.assertEqual((offset['pairs'], offset['exact_matches']), (2, 2))


if __name__ == '__main__': unittest.main()
