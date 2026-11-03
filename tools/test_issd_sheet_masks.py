import unittest
from PIL import Image
from compare_issd_sheet_masks import compare_masks, compare_sheets


class SheetMaskTests(unittest.TestCase):
    def test_translated_shape_and_extra_pixel(self):
        a={(0,0),(1,0),(0,1)}
        b={(4,5),(5,5),(4,6)}
        self.assertTrue(compare_masks(a,b)['identical_up_to_translation'])
        result=compare_masks(a,b|{(10,10)})
        self.assertEqual(result['candidate_only'],1)
        self.assertFalse(result['identical_up_to_translation'])

    def test_rejects_wrong_dimensions(self):
        with self.assertRaises(ValueError):
            compare_sheets(Image.new('RGBA',(2,2)),Image.new('RGBA',(2,2)),(2,2),(2,2),2)


if __name__=='__main__': unittest.main()
