import unittest
from PIL import Image
from audit_issd_candidate_occlusion import classify


class CandidateOcclusionTests(unittest.TestCase):
    def test_explains_only_matching_front_pixel(self):
        image=Image.new('RGB',(256,224))
        image.putpixel((1,1),(0,0,255))
        image.putpixel((2,2),(0,255,0))
        result=classify({(1,1):(255,0,0),(2,2):(255,0,0)},
                        {(1,1):(0,0,255),(2,2):(0,0,255)},image)
        self.assertEqual(result['mismatches_explained_by_earlier_slots'],1)
        self.assertEqual(result['unexplained_mismatches'],1)

    def test_rejects_non_native_screenshot(self):
        with self.assertRaises(ValueError):classify({}, {},Image.new('RGB',(2,2)))


if __name__=='__main__':unittest.main()
