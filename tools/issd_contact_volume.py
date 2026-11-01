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


def contact_volume(words, actor, offsets, ball, *, phase, flag_11fa, actor_flags, entry='FAEA', actor_link=0):
    """Model FAF1 gates and axis checks; inputs are raw 16-bit words.

    actor, offsets, ball are (x, y, z). Entry selects FAE5, FAEA or FAF1.
    Returns a new actor_flags value; does not mutate emulator memory.
    """
    if len(words)!=6 or any(len(v)!=3 for v in (actor, offsets, ball)):
        raise ValueError('Expected six table words and three coordinates')
    values=tuple(words)+tuple(actor)+tuple(offsets)+tuple(ball)+(phase,flag_11fa,actor_flags,actor_link)
    if any(not isinstance(v,int) or not 0<=v<=0xffff for v in values):
        raise ValueError('Inputs must be unsigned 16-bit words')
    if entry not in ('FAE5','FAEA','FAF1'):
        raise ValueError('Unknown entry point')
    if ((entry=='FAE5' and actor_link!=0) or
        (entry in ('FAE5','FAEA') and actor_flags & 0x0400) or
        phase != 0 or flag_11fa & 0x8000):
        return {'carry':1, 'actor_flags':actor_flags, 'rejected_by':'gate'}
    for i,name in ((2,'z'),(0,'x'),(1,'y')):
        if axis_carry(words[2*i],actor[i],offsets[i],ball[i],words[2*i+1]):
            return {'carry':1, 'actor_flags':actor_flags, 'rejected_by':name}
    return {'carry':0, 'actor_flags':actor_flags|0x0400, 'rejected_by':None}


def prepare_offsets(direction, selectors, offsets_table, vertical_byte):
    """Model FA91's direction lookup and signed byte extension."""
    if not 0<=direction<8 or len(selectors)<8 or not 0<=vertical_byte<=255:
        raise ValueError('Invalid direction, selector table or vertical byte')
    selector=selectors[direction]
    if not 0<=selector<=255: raise ValueError('Invalid selector')
    index=(selector & 0x3f)>>2
    if len(offsets_table)<=index+1: raise ValueError('Offset table too short')
    def signed(value):
        if not 0<=value<=255: raise ValueError('Invalid byte')
        return value if value<128 else value-256
    x,y=signed(offsets_table[index]),signed(offsets_table[index+1])
    if selector&0x80: x=-x
    if selector&0x40: y=-y
    return (x&0xffff,y&0xffff,signed(vertical_byte)&0xffff)


def extract(source, rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    result=[]
    for address in (0x81CF5F,0x81CF83,0x81CF47):
        label=f'DATA_{address:06X}'
        values=table(source,label,2)
        if len(values)!=6: raise ValueError(f'Invalid table length: {label}')
        raw=b''.join(v.to_bytes(2,'little') for v in values)
        offset=0x8000+(address&0x7fff)
        if rom[offset+header:offset+header+len(raw)]!=raw:
            raise ValueError(f'ROM mismatch: {label}')
        result.append({'label':label,'lorom_offset':f'{offset:06X}','words':values})
    offset_table=table(source,'DATA_81CEF6',1)
    offset=0xCEF6
    if len(offset_table)!=9 or rom[header+offset:header+offset+9]!=bytes(offset_table):
        raise ValueError('ROM mismatch: DATA_81CEF6')
    block=source.split('CODE_85FAF1:',1)[1].split('CODE_85FB37:',1)[0]
    required=('ADC.b $10','ADC.b $3C','SBC.w $0410',
              'ADC.b $08','ADC.b $38','SBC.w $0408',
              'ADC.b $0C','ADC.b $3A','SBC.w $040C')
    if not all(fragment in block for fragment in required):
        raise ValueError('Contact routine changed')
    return {'schema':'issd-contact-volume/v1','source':str(ASM.relative_to(ROOT)),
            'rom_sha256':hashlib.sha256(rom).hexdigest(),'tables':result,
            'offset_table':{'label':'DATA_81CEF6','lorom_offset':'00CEF6','bytes':offset_table},
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
    print('Verified three contact tables, one offset table and axis instructions')
