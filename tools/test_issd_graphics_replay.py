import unittest
from analyze_issd_graphics_replay import compare_oam


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


if __name__ == '__main__': unittest.main()
