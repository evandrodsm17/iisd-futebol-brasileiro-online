import json
from pathlib import Path
import unittest
from audit_issd_actor_oam_properties import audit,derive
from audit_issd_match_palette import audit as audit_palette

ROOT=Path(__file__).resolve().parent.parent
CAPTURE=ROOT/'analysis/bsnes-actor-oam-props'
BRIDGE=ROOT/'analysis/bsnes-hair-detail-selector/descriptor-bridge.json'
ROM=ROOT/'International Superstar Soccer Deluxe/International Superstar Soccer Deluxe (USA).sfc'


class ActorOamPropertyTest(unittest.TestCase):
    def test_inherited_and_palette_remap(self):
        row={'object_inherited':0,'global_prop':0x20,'object_prop':0,'object_flags':0x40,'tile_base':2,
             'parts':[{'dx':2,'dy':3,'tile':5,'attr':0x20,'large':False}]}
        result=derive(row,{'draw_x':30,'draw_y':40,'draw_z':0},0,[4])[0]
        self.assertEqual(result,{'slot':4,'x':24,'y':39,'tile':7,'size':8,'attr':0x68})

    @unittest.skipUnless((CAPTURE/'hair-runtime.jsonl').exists() and BRIDGE.exists() and ROM.exists(),'Requires local ROM and capture')
    def test_actor_and_palette_against_replay(self):
        bridge=json.loads(BRIDGE.read_text(encoding='utf8'))
        actors=audit(CAPTURE,bridge)
        detail=json.loads((ROOT/'dist/data/issd-team-detail-colors.json').read_text(encoding='utf8'))
        palettes=audit_palette(ROM.read_bytes(),detail,CAPTURE,bridge)
        self.assertEqual(len(actors['samples']),76);self.assertEqual(len(palettes['samples']),76)
        self.assertEqual(len({s['descriptor'] for s in actors['samples']}),10)


if __name__=='__main__':unittest.main()
