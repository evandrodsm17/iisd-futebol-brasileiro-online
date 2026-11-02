"""Extract charge-action animation pointers and durations from ROM and disassembly."""
import hashlib
import json
import re
from pathlib import Path
from extract_issd_ball_attachment import ASM, ROOT


def extract(source, rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    def block(label):
        return re.split(r'^\w+:',source.split(label+':',1)[1],maxsplit=1,flags=re.M)[0]
    labels=('82CF9F','82CFAF','82CFB7','82CFC7','82CFD7','82CFE7','82CFF7')
    tables={}
    for label in labels:
        text=block('DATA_'+label)
        if label=='82CFAF':
            values=[int(s,16) for s in re.findall(r'\$([0-9A-F]+)',text)]
            raw=bytes(values); width=1
        else:
            tokens=re.findall(r'DATA_82([0-9A-F]{4})(\^\$8000)?',text)
            values=[int(address,16) ^ (0x8000 if flip else 0) for address,flip in tokens]
            raw=b''.join(v.to_bytes(2,'little') for v in values); width=2
        offset=0x10000+(int(label[2:],16)&0x7fff)
        if len(values)!=8 or rom[header+offset:header+offset+len(raw)]!=raw:
            raise ValueError(f'ROM mismatch or invalid length: {label}')
        tables[label]={'offset':f'{offset:06X}','width':width,'values':values}
    return {'schema':'issd-charge-animation/v1','source':str(ASM.relative_to(ROOT)),
            'rom_sha256':hashlib.sha256(rom).hexdigest(),'tables':tables,
            'limitations':['Direction indices are native, not mapped to screen.',
                           'Duration counts depend on handler cadence.',
                           'Descriptor bytes, OAM composition and visual action remain unvalidated.']}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'dist/data/issd-charge-animation.json')
    args=p.parse_args()
    data=extract(ASM.read_text(encoding='utf-8'),args.rom.read_bytes())
    args.output.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print('Verified seven animation tables against ROM')
