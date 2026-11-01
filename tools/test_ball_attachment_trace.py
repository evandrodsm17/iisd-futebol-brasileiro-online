import unittest
from analyze_issd_ball_attachment_trace import analyze, rom_tables


class AttachmentTraceTests(unittest.TestCase):
    def test_wrapped_coordinate_and_consecutive_transition(self):
        def row(frame,state):
            return {'frame':frame,'globals':{'0408':3,'040C':9},'actors':[
                {'address':0x500,'words':{'0032':state,'002E':0,'0008':65530,'000C':10}}]}
        fixed=[(9,-1)]*8; cycle=[[(9,-1)]*8]*8
        result=analyze([row(1,0xB8),row(2,0xC0),row(4,0xE0)],fixed,cycle)
        self.assertEqual(result['by_state']['00B8']['fixed_pair_matches'],1)
        self.assertEqual(result['state_transitions'],[{'from':'00B8','to':'00C0','count':1}])

    def test_direction_signs_and_header(self):
        rom=bytearray(0x10000)
        rom[0x9623:0x962B]=bytes([0,0x80,0x40,0xC0,0,0,0,0])
        rom[0x9842:0x9862]=bytes([3]*32)
        rom[0x9862:0x9882]=bytes([5]*32)
        for header in (b'',bytes(512)):
            _,cycle,_=rom_tables(header+rom)
            self.assertEqual([x[0] for x in cycle[:4]],[(3,5),(-3,5),(3,-5),(-3,-5)])

    def test_turn_words_and_both_signs(self):
        rom=bytearray(0x10000)
        rom[0x9802:0x9806]=bytes.fromhex('feff0500')
        _,_,turn=rom_tables(rom)
        self.assertIn((-2,5),turn)
        self.assertIn((2,-5),turn)

    def test_repeated_frame_rejected(self):
        row={'frame':1,'globals':{'0408':0,'040C':0},'actors':[]}
        with self.assertRaises(ValueError): analyze([row,row],[],[])


if __name__=='__main__': unittest.main()
