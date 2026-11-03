"""Extract body pose geometry from the ROM's compressed match resources."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import decompress

# DATA_82:8C36, sources and destinations in the match geometry loader.
RESOURCES=((0x988472,0x4000),(0x988099,0x424a),(0x988138,0x42d4),
           (0x9882c6,0x449e),(0x988000,0x4626),(0x9885e2,0x46a8),
           (0x9886b8,0x472a),(0x988846,0x490a),(0x9888be,0x4988),(0x988cb0,0x4bac))


def extract(rom,hair_geometry):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    rom=rom[header:];rawposes={}
    for source,destination in RESOURCES:
        data,interleaved=decompress(rom,source);frames=data[0];count=int.from_bytes(data[1:3],'little');start=3+frames
        if interleaved or len(data)!=start+count*4 or sum(data[3:start])!=count:raise ValueError(f'Unexpected geometry resource {source:06X}')
        cursor=0
        for length in data[3:start]:
            if not length:raise ValueError('Empty frame')
            parts=[]
            for i in range(cursor,cursor+length):
                x,y,tile,attr=(data[start+count*plane+i] for plane in range(4))
                signed=lambda b:(b if b<128 else b-256)&0xffff
                parts.append({'dx':signed(x),'dy':signed(y),'tile':tile,'attr':attr&0xef,'large':bool(attr&0x10)})
            pointer=destination+cursor*2
            if pointer in rawposes:raise ValueError('Overlapping geometry resources')
            rawposes[pointer]={'source':f'${source:06X}','parts':parts};cursor+=length
    poses={}
    for item in hair_geometry['poses'].values():
        desc=item['descriptor'];offset=0x10000+(desc&0x7fff);pointer=int.from_bytes(rom[offset:offset+2],'little')
        if pointer not in rawposes:raise ValueError(f'Missing geometry {desc:04X}: {pointer:04X}')
        poses[str(desc)]={'descriptor':desc,'pointer':pointer,**rawposes[pointer]}
    if len(poses)!=90:raise ValueError('Unexpected descriptor count')
    return {'schema':'issd-locomotion-body-geometry/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'poses':poses,'limitations':['Geometry alone does not establish actor properties, OAM slots, palette, or gameplay timing.',
            'Same-frame OAM comparison is available only for a subset of these descriptors.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('hair_geometry',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=extract(a.rom.read_bytes(),json.loads(a.hair_geometry.read_text(encoding='utf8')))
    a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Extracted {len(r['poses'])} body geometries")
