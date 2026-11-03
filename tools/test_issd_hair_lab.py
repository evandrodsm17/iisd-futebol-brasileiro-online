import tempfile
from pathlib import Path
import unittest
from PIL import Image
from export_issd_hair_lab import export,SIZE

ROOT=Path(__file__).resolve().parent.parent/'analysis'
CASES=[(1,ROOT/'bsnes-hair-oam-clear'),(2,ROOT/'bsnes-hair-style2'),(13,ROOT/'bsnes-hair-style13')]


@unittest.skipUnless(all((p/'hair-runtime.jsonl').exists() for _,p in CASES),'Requires private emulator captures')
class HairLabTest(unittest.TestCase):
    def test_layered_export_and_distinct_hair(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder);result=export(CASES,out)
            self.assertEqual([x['frames'] for x in result['styles']],[13,13,13])
            images=[]
            for style in result['styles']:
                with Image.open(out/style['body']) as body,Image.open(out/style['hair']) as hair:
                    self.assertEqual(body.size,(13*SIZE,SIZE));self.assertEqual(hair.size,body.size)
                    self.assertIsNotNone(body.getchannel('A').getbbox());self.assertIsNotNone(hair.getchannel('A').getbbox())
                    combined=body.copy();combined.alpha_composite(hair);self.assertIsNotNone(combined.getchannel('A').getbbox())
                    images.append(hair.tobytes())
            self.assertNotEqual(images[0],images[1]);self.assertNotEqual(images[1],images[2])


if __name__=='__main__':unittest.main()
