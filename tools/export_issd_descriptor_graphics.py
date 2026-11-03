"""Export local indexed graphics rows referenced by ROM locomotion descriptors."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def export(rom,geometry,detail_report=None):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected original USA ROM')
    rom=rom[header:]
    if geometry.get('schema')!='issd-hair-locomotion-geometry/v1':raise ValueError('Unexpected geometry schema')
    descriptors={}
    actors={}
    if detail_report:
        if detail_report.get('schema')!='issd-uniform-detail-replay/v1' or detail_report['rom_sha256']!=hashlib.sha256(rom).hexdigest():raise ValueError('Incompatible detail report')
        for row in detail_report['frames']:
            previous=actors.setdefault(row['descriptor'],row['actor'])
            if previous!=row['actor']:raise ValueError('Ambiguous actor detail fields')
    for item in geometry['poses'].values():
        descriptor=item['descriptor']
        actor=actors.get(descriptor);vram,meta=descriptor_tiles(rom,descriptor,actor)
        descriptors[str(descriptor)]={'pose':meta['pose'],'row_bytes':meta['row_bytes'],'detail':meta['detail'],
                                      'detail_validated':actor is not None,
                                      'tiles_base64':base64.b64encode(vram).decode('ascii')}
    return {'schema':'issd-descriptor-graphics-local/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'descriptors':descriptors,'limitations':['Uniform detail tile is only validated for descriptors covered by the optional detail report.',
             'The descriptor rows alone do not supply OAM positions, banks, palettes or action timing.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('rom',type=Path);parser.add_argument('geometry',type=Path)
    parser.add_argument('--detail-report',type=Path,help='Optional same-replay actor detail evidence')
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    report=json.loads(args.detail_report.read_text(encoding='utf8')) if args.detail_report else None
    data=export(args.rom.read_bytes(),json.loads(args.geometry.read_text(encoding='utf8')),report)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    print(f"Exported graphics for {len(data['descriptors'])} descriptors locally")
