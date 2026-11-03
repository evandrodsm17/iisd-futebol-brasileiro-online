"""Export local indexed graphics rows referenced by ROM locomotion descriptors."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def export(rom,geometry):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected original USA ROM')
    rom=rom[header:]
    if geometry.get('schema')!='issd-hair-locomotion-geometry/v1':raise ValueError('Unexpected geometry schema')
    descriptors={}
    for item in geometry['poses'].values():
        descriptor=item['descriptor']
        vram,meta=descriptor_tiles(rom,descriptor)
        descriptors[str(descriptor)]={'pose':meta['pose'],'row_bytes':meta['row_bytes'],'detail':meta['detail'],
                                      'tiles_base64':base64.b64encode(vram).decode('ascii')}
    return {'schema':'issd-descriptor-graphics-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'descriptors':descriptors,'limitations':['Uniform detail tile is not populated: it depends on actor and kit state.',
             'The descriptor rows alone do not supply OAM positions, banks, palettes or action timing.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path);parser.add_argument('geometry',type=Path)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    data=export(args.rom.read_bytes(),json.loads(args.geometry.read_text(encoding='utf8')))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    print(f"Exported graphics for {len(data['descriptors'])} descriptors locally")
