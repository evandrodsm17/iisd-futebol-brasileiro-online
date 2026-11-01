"""Verify actor ball-placement state rows against assembly and local ROM."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from extract_issd_ball_attachment import ASM, ROOT


def extract(source, rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    body=source.split('DATA_81BD58:',1)[1]
    lines=[]
    for line in body.splitlines():
        if re.match(r'^\w+:',line): break
        if line.strip().startswith('dw '): lines.append(line.strip()[3:])
    states=[]
    for state in (0xB8,0xC0,0xC8,0xD8):
        fields=lines[state//8].split(',')
        values=[int(v.removeprefix('CODE_84').removeprefix('$'),16) for v in fields]
        raw=b''.join(v.to_bytes(2,'little') for v in values)
        offset=0xBD58+state
        if rom[header+offset:header+offset+8]!=raw:
            raise ValueError(f'State {state:04X}: ROM mismatch')
        states.append({'state':f'{state:04X}','lorom_offset':f'{offset:06X}',
                       'handlers':fields[:3],'flags':fields[3],'rom_verified':True})
    excerpts=[]
    for start,end in [('84854E','848566'),('848DD1','848E1C'),
                      ('848E1C','848E3D'),('848E58','848EA9'),
                      ('848EA9','848EED'),('80DD31','80DD47'),
                      ('85F8B9','85F91D'),('8394A4','83956E'),
                      ('848056','84809E'),('8486F6','84873E'),
                      ('84BD0A','84BD0F'),('84C25E','84C26A'),
                      ('84C2AC','84C2CB'),('848F6A','848FA5'),
                      ('848FA8','848FE8'),('84909D','8490FF')]:
        block=source.split('CODE_'+start+':',1)[1].split('CODE_'+end+':',1)[0].strip()
        excerpts.append({'label':'CODE_'+start,'assembly_excerpt':block})
    return {'schema':'issd-ball-state-routing/v1','source':str(ASM.relative_to(ROOT)),
            'rom_sha256':hashlib.sha256(rom).hexdigest(),'states':states,
            'routines':excerpts,
            'limitations':['Handler columns retain their source order; no CPU/human role inferred.',
                          'State names remain descriptive paths, not a complete possession model.',
                          'Balanced PHX/PLX proves X preservation on normal returning paths, not arbitrary corrupted states.',
                          'No frame cadence or Canvas scaling inferred.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'dist/data/issd-ball-state-routing.json')
    args=p.parse_args()
    result=extract(ASM.read_text(encoding='utf-8'),args.rom.read_bytes())
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Verified four state rows against ROM:',args.output)
