"""Audit auxiliary locomotion geometry against an isolated match snapshot."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5
from extract_issd_flags import decompress

RESOURCES=((0x4e68,0x989109),(0x4ed0,0x989165),(0x4eee,0x989189),
           (0x4f0c,0x9891b2),(0x4f5c,0x9891fd),(0x4f98,0x989239))


def build(rom, scripts, snapshot):
    header=len(rom)%0x8000
    if header not in (0,512) or hashlib.md5(rom[header:]).hexdigest()!=EXPECTED_MD5:
        raise ValueError('Expected original USA ROM')
    data=rom[header:]
    observed={}
    for row in snapshot:
        if row['pointer'] in observed:raise ValueError('Duplicate WRAM pointer')
        observed[row['pointer']]=row
    entries={}
    for dest,source in RESOURCES:
        raw,interleaved=decompress(data,source)
        count=int.from_bytes(raw[1:3],'little');frames=raw[0];start=3+frames
        if interleaved or frames!=count or len(raw)!=start+count*4 or any(x!=1 for x in raw[3:start]):
            raise ValueError(f'Unexpected geometry format ${source:06X}')
        for i in range(count):
            values=[raw[start+count*j+i] for j in range(4)]
            x,y,tile,attr=values
            signed=lambda n:n if n<128 else n-256
            pointer=dest+i*2
            expected={'pointer':pointer,'x_word':signed(x)&0xffff,'y_word':signed(y)&0xffff,'tile':tile,'attr':attr}
            if observed.get(pointer)!=expected:raise ValueError(f'Geometry mismatch ${pointer:04X}')
            entries[pointer]={'pointer':pointer,'x':signed(x),'y':signed(y),'tile':tile,'attr':attr,
                              'source':f'${source:06X}'}
    if set(entries)!=set(observed):raise ValueError('Snapshot coverage mismatch')
    poses={};cycles={}
    for name,cycle in scripts['cycles'].items():
        if name not in ('walking','running'):continue
        cycles[name]=[]
        for direction in cycle['directions']:
            descriptors=direction['descriptors']
            cycles[name].append({'direction':direction['direction'],'descriptors':descriptors})
            for desc in descriptors:
                offset=0x10000+(desc&0x7fff)
                pointer=int.from_bytes(data[offset+6:offset+8],'little');selector=data[offset+8]
                if pointer not in entries or not 1<=selector<=24:
                    raise ValueError(f'Unsupported auxiliary descriptor ${desc:04X}')
                poses[str(desc)]={'descriptor':desc,'selector':selector,**entries[pointer]}
    if set(cycles)!={'walking','running'} or len(poses)!=90:
        raise ValueError('Unexpected locomotion descriptor coverage')
    return {'schema':'issd-hair-locomotion-geometry/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'snapshot_entries_verified':len(entries),'unique_descriptors':len(poses),'cycles':cycles,'poses':poses,
            'limitations':['Geometry bytes match WRAM but do not establish the final OAM palette or layering.',
                           'Hair atlas selection and dynamic VRAM transfers require same-frame gameplay validation.',
                           'No visual asset or ROM is included.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('rom',type=Path);p.add_argument('scripts',type=Path)
    p.add_argument('snapshot',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    raw=a.snapshot.read_bytes();result=build(a.rom.read_bytes(),json.loads(a.scripts.read_text(encoding='utf8')),
                                            [json.loads(line) for line in raw.splitlines() if line.strip()])
    result['snapshot_sha256']=hashlib.sha256(raw).hexdigest()
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(f"Verified {result['snapshot_entries_verified']} WRAM entries and {result['unique_descriptors']} descriptors")
