import unittest
from extract_issd_ball_attachment import extract


class AttachmentTests(unittest.TestCase):
    def fixture(self):
        source=''
        rom=bytearray(0x10000)
        for addr,count,width in [(0x8197C2,16,2),(0x8197E2,16,2),(0x819802,32,2),(0x819842,64,1)]:
            values=[i for i in range(count)]
            source+=f'DATA_{addr:06X}:\n\tdw '+','.join(f'${v:04X}' for v in values)+'\nNEXT:\n'
            raw=b''.join(v.to_bytes(width,'little') for v in values)
            offset=0x8000+(addr&0x7FFF)
            rom[offset:offset+len(raw)]=raw
        for start,end in [('80DE3D','80DE55'),('80DE55','80DE6D'),('80DEA5','80DEB9'),('80DF00','80DF37'),('8497FE','849818'),('85ECC3','85ECDE')]:
            source+=f'CODE_{start}:\nRTL\nCODE_{end}:\n'
        return source,bytes(rom)

    def test_both_header_formats(self):
        source,rom=self.fixture()
        for header in (b'',bytes(512)):
            self.assertEqual(len(extract(source,header+rom)['tables']),4)

    def test_mismatch_rejected(self):
        source,rom=self.fixture()
        changed=bytearray(rom);changed[0x97C2]^=1
        with self.assertRaisesRegex(ValueError,'ROM mismatch'):
            extract(source,bytes(changed))


if __name__=='__main__': unittest.main()
