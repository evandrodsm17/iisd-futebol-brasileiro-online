import unittest
from extract_issd_ball_states import extract


class BallStateTests(unittest.TestCase):
    def fixture(self):
        rows=['dw CODE_848E1C,CODE_84C13F,CODE_84C26A,$0320']*28
        source='DATA_81BD58:\n'+'\n'.join(rows)+'\nEND:\n'
        for start,end in [('84854E','848566'),('848DD1','848E1C'),('848E1C','848E3D'),('848E58','848EA9'),('848EA9','848EED'),('80DD31','80DD47'),('85F8B9','85F91D'),('8394A4','83956E')]:
            source+=f'CODE_{start}:\nRTL\nCODE_{end}:\n'
        for start,end in [('848056','84809E'),('8486F6','84873E'),('84BD0A','84BD0F'),('84C25E','84C26A'),('84C2AC','84C2CB'),('848F6A','848FA5'),('848FA8','848FE8'),('84909D','8490FF')]:
            source+=f'CODE_{start}:\nRTL\nCODE_{end}:\n'
        rom=bytearray(0x10000)
        for state in (0xB8,0xC0,0xC8,0xD8):
            rom[0xBD58+state:0xBD60+state]=bytes.fromhex('1c8e3fc16ac22003')
        return source,bytes(rom)

    def test_header_and_rows(self):
        source,rom=self.fixture()
        for header in (b'',bytes(512)):
            self.assertEqual(len(extract(source,header+rom)['states']),4)

    def test_mismatch_rejected(self):
        source,rom=self.fixture()
        with self.assertRaisesRegex(ValueError,'ROM mismatch'):
            extract(source,bytes(len(rom)))


if __name__=='__main__': unittest.main()
