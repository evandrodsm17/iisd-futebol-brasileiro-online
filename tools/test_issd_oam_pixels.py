import unittest
from PIL import Image
from compare_issd_oam_pixels import compose, compare, ppu_color


class OamPixelsTests(unittest.TestCase):
    def test_obj_palette_and_transparent_pixels(self):
        oam = bytes(544)
        vram = bytearray(65536)
        vram[0] = 0x80
        cgram = bytearray(512)
        cgram[129 * 2] = 0x1f  # OBJ palette 0, index 1: red
        pixels = compose(oam, vram, cgram, 0, [0])
        self.assertEqual(pixels, {(0, 0): (255, 0, 0)})
        image = Image.new('RGB', (256, 224))
        image.putpixel((0, 0), (255, 0, 0))
        self.assertEqual(compare(pixels, image)['exact_rgb_matches'], 1)

    def test_rejects_duplicates(self):
        with self.assertRaises(ValueError): compose(bytes(544), bytes(65536), bytes(512), 0, [2, 2])

    def test_five_bit_color_uses_bit_replication(self):
        cgram = bytearray(512)
        cgram[0] = 16
        self.assertEqual(ppu_color(cgram, 0), (132, 0, 0))


if __name__ == '__main__': unittest.main()
