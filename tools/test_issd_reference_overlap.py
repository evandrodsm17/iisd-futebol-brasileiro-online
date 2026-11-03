import unittest
from PIL import Image
from audit_issd_reference_overlap import classify


class ReferenceOverlapTests(unittest.TestCase):
    def test_only_counts_same_reference_color(self):
        image=Image.new('RGB',(256,224)); reference=Image.new('RGB',(256,224))
        image.putpixel((1,1),(2,3,4));reference.putpixel((1,1),(2,3,4))
        image.putpixel((2,2),(8,8,8))
        result=classify({(1,1):(9,9,9),(2,2):(9,9,9)},image,reference)
        self.assertEqual(result['unmatched_matching_reference'],1)
        self.assertEqual(result['remaining_unmatched'],1)

    def test_rejects_wrong_screenshot_size(self):
        with self.assertRaises(ValueError):classify({},Image.new('RGB',(1,1)),Image.new('RGB',(256,224)))


if __name__=='__main__':unittest.main()
