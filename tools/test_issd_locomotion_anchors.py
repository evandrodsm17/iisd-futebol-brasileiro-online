import json
from pathlib import Path
import unittest
from PIL import Image
from extract_issd_locomotion_anchors import extract
from export_issd_team_motion import renderer, trace

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'
TRACE=ROOT/'docs'/'issd-match-trace-coverage.jsonl'
ASSETS=ROOT/'dist'/'assets'/'issd'/'oam-teams'
CATALOG=ROOT/'dist'/'data'/'issd-rom-catalog.json'


@unittest.skipUnless(ROM.exists() and TRACE.exists() and ASSETS.exists(),'Requires local ROM and generated sheets')
class LocomotionAnchorsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM.read_bytes();cls.rows=trace(TRACE);cls.anchors=extract(cls.rom,cls.rows,0x0d00)
        cls.catalog=json.loads(CATALOG.read_text(encoding='utf8'));cls.r=renderer()

    def test_reproduces_original_sheet_pixels(self):
        for team,kit,motion,direction in ((0,'home','running',0),(30,'away','running',6),
                                          (2,'home','walking',2),(31,'away','walking',5)):
            with self.subTest(team=team,kit=kit,motion=motion,direction=direction):
                entry=self.anchors['cycles'][motion][direction];w,h=entry['cell_width'],entry['cell_height']
                palette=self.catalog['teams'][team]['kit'][kit]['sprite_palette']
                banks={i:self.r.parse_palette(palette) for i in range(8)}
                reconstructed=Image.new('RGBA',(w*len(entry['frames']),h))
                for index,meta in enumerate(entry['frames']):
                    actor=next(a for row in self.rows for a in row['actors'] if a['address']==0x0d00
                               and a['direction']==direction and a['descriptor']==meta['descriptor'])
                    vram,_=self.r.descriptor_tiles(self.rom,meta['descriptor'],actor)
                    image=self.r.compose(vram,actor['parts'],banks)
                    reconstructed.alpha_composite(image,(index*w+meta['origin_x']+meta['left'],meta['origin_y']+meta['top']))
                with Image.open(ASSETS/f'{team:02d}'/kit/f'{motion}-{direction}.png') as existing:
                    # Compare all channels; getbbox on an RGBA difference can ignore RGB under zero alpha.
                    self.assertEqual(reconstructed.tobytes(),existing.convert('RGBA').tobytes())

    def test_missing_runtime_pose_fails(self):
        with self.assertRaisesRegex(ValueError,'Missing captured pose'):
            extract(self.rom,[],0x0d00)


if __name__=='__main__':unittest.main()
