import unittest
from render_issd_oam_composite import decode_tile


class OamTileTests(unittest.TestCase):
    def test_4bpp_decodes_obj_base_above_511(self):
        vram = bytearray(65536)
        offset = 0x600 * 32
        vram[offset] = 0x80
        vram[offset + 16] = 0x80
        pixels = decode_tile(vram, 0x600)
        self.assertEqual(pixels[0][0], 5)
        self.assertEqual(pixels[0][1], 0)
        self.assertEqual(decode_tile(vram, 0)[0][0], 0)


if __name__ == '__main__': unittest.main()
