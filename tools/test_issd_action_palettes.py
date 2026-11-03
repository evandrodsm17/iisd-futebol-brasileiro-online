import unittest
from audit_issd_action_palettes import palette_hex,matches


class ActionPalettesTests(unittest.TestCase):
    def test_obj_palette_and_exact_matching(self):
        cgram=bytearray(512);cgram[2*144]=31
        palette=palette_hex(cgram,1)
        self.assertEqual(palette[0],'#FF0000')
        teams=[{'id':2,'name':'Example','kit':{'home':{'sprite_palette':palette},'away':{'sprite_palette':['#000000']*16}}}]
        self.assertEqual(matches(palette,teams),[{'team_id':2,'team_name':'Example','kit':'home'}])

    def test_rejects_invalid_cgram_or_bank(self):
        with self.assertRaises(ValueError):palette_hex(bytes(512),8)
        with self.assertRaises(ValueError):palette_hex(bytes(511),0)


if __name__=='__main__':unittest.main()
