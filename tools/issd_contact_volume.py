"""Static 65C816 word arithmetic for one axis of the native contact test."""
import hashlib
import json
from pathlib import Path
from extract_issd_ball_release import table, ASM, ROOT


def axis_carry(base, actor, offset, ball, limit):
    # CLC ADC actor; CLC ADC offset; SBC ball; SEC SBC limit.
    first=(base+actor)&0xffff
    total=first+offset
    value=total&0xffff
    carry=int(total>0xffff)
    difference=value-ball-(1-carry)
    value=difference&0xffff
    final=value-limit
    return int(final>=0)


def extract(source, rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    result=[]
    for address in (0x81CF5F,0x81CF83):
        label=f'DATA_{address:06X}'
        values=table(source,label,2)
        if len(values)!=6: raise ValueError(f'Invalid table length: {label}')
        raw=b''.join(v.to_bytes(2,'little') for v in values)
        offset=0x8000+(address&0x7fff)
        if rom[offset+header:offset+header+len(raw)]!=raw:
            raise ValueError(f'ROM mismatch: {label}')
        result.append({'label':label,'lorom_offset':f'{offset:06X}','words':values})
    block=source.split('CODE_85FAF1:',1)[1].split('CODE_85FB37:',1)[0]
    required=('ADC.b $10','ADC.b $3C','SBC.w $0410',
              'ADC.b $08','ADC.b $38','SBC.w $0408',
              'ADC.b $0C','ADC.b $3A','SBC.w $040C')
    if not all(fragment in block for fragment in required):
        raise ValueError('Contact routine changed')
    return {'schema':'issd-contact-volume/v1','source':str(ASM.relative_to(ROOT)),
            'rom_sha256':hashlib.sha256(rom).hexdigest(),'tables':result,
            'arithmetic':'CLC ADC actor; CLC ADC offset; SBC ball; SEC SBC limit',
            'limitations':['Axis carry alone is not a complete possession test.',
                           'Offsets and state gates require call-site context.',
                           'No Canvas unit conversion or runtime application.']}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(); p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'dist/data/issd-contact-volume.json')
    args=p.parse_args()
    result=extract(ASM.read_text(encoding='utf-8'),args.rom.read_bytes())
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Verified two contact tables and axis instructions')
