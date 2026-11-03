import unittest
from PIL import Image
from audit_issd_slot_layers import audit


class SlotLayerTests(unittest.TestCase):
    def test_reports_overlapping_palette_banks(self):
        oam=bytearray(544);oam[3]=2; oam[7]=0
        vram=bytearray(65536);vram[0]=0x80
        cgram=bytearray(512);cgram[(128+16+1)*2]=31
        screenshot=Image.new('RGB',(256,224));screenshot.putpixel((0,0),(255,0,0))
        result=audit(oam,vram,cgram,0,[0,1],screenshot)
        self.assertEqual(result['overlaps'][0]['overlap_pixels'],1)
        self.assertEqual(result['slots'][0]['palette_bank'],1)
        self.assertEqual(result['slots'][0]['exact_rgb_matches'],1)
        self.assertEqual(result['slots'][1]['nonmatching_pixels'],1)


if __name__=='__main__':unittest.main()
