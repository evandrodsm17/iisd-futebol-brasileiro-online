import unittest
from pathlib import Path
from compare_issd_replay_oam_frames import audit


class ReplayOamFramesTests(unittest.TestCase):
    def test_rejects_unexpected_callback_timing(self):
        draw=[{'type':'draw_entry','step':1,'frame':20,'object':0x1900,'stack':0x34f,'list_y':0x1d42},
              {'type':'draw_entry','step':1,'frame':20,'object':0x400,'stack':0x337,'list_y':0x1d44}]
        graphics=[{'step':1,'frame':23}]
        with self.assertRaises(ValueError): audit(draw,graphics,Path('.'),0x1900)

    def test_rejects_duplicate_frame(self):
        with self.assertRaises(ValueError):
            audit([], [{'step':1,'frame':2},{'step':2,'frame':2}], Path('.'), 0x1900)


if __name__=='__main__': unittest.main()
