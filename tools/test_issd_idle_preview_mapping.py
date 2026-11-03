import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent.parent
ROM=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'
SCRIPTS=ROOT/'dist/data/issd-action-scripts.json'


class IdlePreviewMappingTest(unittest.TestCase):
    @unittest.skipUnless(ROM.exists(),'Requires original local ROM')
    def test_editor_descriptors_match_first_idle_descriptor(self):
        rom=ROM.read_bytes();header=len(rom)%0x8000
        if header==512:rom=rom[512:]
        scripts=json.loads(SCRIPTS.read_text(encoding='utf8'))['actions']['idle']['directions']
        mapping=[6,7,0,1,2,3,4,5]
        for direction,index in enumerate(mapping):
            desc=int.from_bytes(rom[0xed1d+index*2:0xed1f+index*2],'little')
            self.assertEqual(desc,scripts[direction]['descriptors'][0])


if __name__=='__main__':unittest.main()
