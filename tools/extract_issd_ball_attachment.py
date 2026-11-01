"""Extract actor-relative ball tables; verify bytes against the local USA ROM."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASM = ROOT / 'YFs_InternationalSuperstarSoccerDeluxe_Disassembly/International_Superstar_Soccer_Deluxe/Routine_Macros_ISSD.asm'


def extract(source, rom):
    header = len(rom) % 0x8000
    if header not in (0, 512):
        raise ValueError('Unsupported ROM size/header')
    tables = []
    for address, count, width in [(0x8197C2,16,2),(0x8197E2,16,2),
                                   (0x819802,32,2),(0x819842,64,1)]:
        label = f'DATA_{address:06X}'
        match = re.search(rf'^{label}:\s*\n(.*?)(?=^\w+:)', source, re.M | re.S)
        values = [int(v,16) for v in re.findall(r'\$([0-9A-F]+)', match[1])]
        if len(values) != count:
            raise ValueError(f'Unexpected table length: {label}')
        data = b''.join(v.to_bytes(width,'little') for v in values)
        offset = ((address >> 16) & 0x7F)*0x8000 + (address & 0x7FFF)
        if rom[offset+header:offset+header+len(data)] != data:
            raise ValueError(f'ROM mismatch: {label}')
        signed = [v if v < 1 << (width*8-1) else v-(1 << (width*8)) for v in values]
        tables.append({'label':label, 'lorom_offset':f'{offset:06X}',
                       'element_bytes':width, 'values':values,
                       'signed_values':signed, 'rom_verified':True})
    routines = []
    for start,end in [('80DE3D','80DE55'),('80DE55','80DE6D'),
                      ('80DEA5','80DEB9'),('80DF00','80DF37'),
                      ('8497FE','849818'),('85ECC3','85ECDE')]:
        excerpt=source.split(f'CODE_{start}:',1)[1].split(f'CODE_{end}:',1)[0].strip()
        routines.append({'label':f'CODE_{start}','assembly_excerpt':excerpt})
    return {'schema':'issd-ball-attachment/v1','source':str(ASM.relative_to(ROOT)),
            'rom_sha256':hashlib.sha256(rom).hexdigest(), 'copier_header_bytes':header,
            'tables':tables,'routines':routines,
            'limitations':['Static call paths are not a complete possession state machine.',
                          'Direction indices are native; no screen-direction mapping inferred.',
                          'Four calls per phase is not automatically four rendered frames.',
                          '$00A6 is an actor link in these paths, not universal proof of possession.',
                          'No Canvas unit conversion or gameplay constants changed.']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'dist/data/issd-ball-attachment.json')
    args=p.parse_args()
    result=extract(ASM.read_text(encoding='utf-8'),args.rom.read_bytes())
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Verified four ball-attachment tables against ROM; wrote',args.output)
