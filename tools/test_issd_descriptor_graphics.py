import base64
import json
from pathlib import Path
import unittest
from export_issd_descriptor_graphics import export
from render_issd_descriptor_sprite import descriptor_tiles

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe'/'International Superstar Soccer Deluxe (USA).sfc'


class DescriptorGraphicsTest(unittest.TestCase):
    def test_invalid_rom_is_rejected(self):
        with self.assertRaises(ValueError):export(bytes(0x8000),{})

    @unittest.skipUnless(ROM.exists(),'Requires local ROM')
    def test_all_locomotion_rows_match_rom_descriptor_reader(self):
        rom=ROM.read_bytes();geometry=json.loads((ROOT/'dist/data/issd-hair-locomotion-geometry.json').read_text(encoding='utf8'))
        result=export(rom,geometry)
        self.assertEqual(len(result['descriptors']),90)
        for key,entry in result['descriptors'].items():
            expected,meta=descriptor_tiles(rom,int(key))
            self.assertEqual(base64.b64decode(entry['tiles_base64']),expected)
            self.assertEqual(entry['row_bytes'],meta['row_bytes'])


if __name__=='__main__':unittest.main()
