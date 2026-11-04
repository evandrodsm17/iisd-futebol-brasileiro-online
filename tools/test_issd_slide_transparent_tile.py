"""Check the transparent ROM detail DMA and its locally exported variants."""
import argparse, base64, json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles, span
import hashlib

def verify(rom, data):
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    blank=span(rom,0x98f014,32)
    if blank!=bytes(32): raise ValueError('$98:F014 is no longer transparent')
    count=0
    for direction,flags in ((3,0),(4,0),(5,0x40)):
        for frame in data['cycles'][str(direction)]:
            if 'detail_variants' not in frame: continue
            for team in (2,18,22,35):
                for shirt in range(1,21):
                    actor={'type':6,'kit_variant':(shirt-1)*2,'uniform_selector':team*2,'object_flags':flags}
                    tiles,meta=descriptor_tiles(rom,frame['descriptor'],actor)
                    if meta['detail_source']!='$F014' or tiles[23*32:24*32]!=blank: raise ValueError('Unexpected DMA source')
                    index=frame['detail_variants'][team*20+shirt-1]
                    if index is None or base64.b64decode(data['detail_pool'][index],validate=True)!=blank: raise ValueError('Invalid exported tile')
                    count+=1
    return count

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True);parser.add_argument('--directions',type=Path,required=True)
    args=parser.parse_args();print('OK: transparent ROM DMA variants:',verify(args.rom.read_bytes(),json.loads(args.directions.read_text(encoding='utf8'))))
