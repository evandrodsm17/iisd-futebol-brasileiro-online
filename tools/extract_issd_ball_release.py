"""Recover release parameters and controller routing with ROM table checks."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from extract_issd_ball_attachment import ASM, ROOT


def update_control_charge(held_buttons, active_mask, counter):
    """Model 80:DA68 on raw words; returns updated counter and mask."""
    if any(not isinstance(v,int) or not 0<=v<=0xffff for v in (held_buttons,active_mask,counter)):
        raise ValueError('Expected unsigned 16-bit words')
    if held_buttons & active_mask and counter < 11:
        return {'counter':counter+1,'active_mask':active_mask}
    return {'counter':counter,'active_mask':0}


def ball_parameter(ball_type, parameter_y, speed_table):
    """Model 83:94D4..94F3; inputs are raw words, output is not Canvas speed."""
    if any(not isinstance(v,int) or not 0<=v<=0xffff for v in (ball_type,parameter_y)):
        raise ValueError('Expected unsigned 16-bit words')
    parameter=min(parameter_y & 0x0f,11)
    index=((ball_type << 4)+parameter)&0xffff
    if index>=len(speed_table): raise ValueError('Index outside verified table')
    return {'type_0430':ball_type,'parameter_0456':parameter,
            'table_index':index,'value_0464':speed_table[index]}


def table(source, label, width):
    block=source.split(label+':',1)[1]
    block=re.split(r'^\w+:',block,maxsplit=1,flags=re.M)[0]
    values=[]
    for line in block.splitlines():
        line=line.strip()
        if not line.startswith('db ' if width==1 else 'dw '): continue
        for token in line[3:].split(','):
            token=token.strip()
            if token.startswith('DATA_'): value=int(token[5:],16)
            elif re.fullmatch(r'\$[0-9A-F]+',token): value=int(token[1:],16)
            else: raise ValueError(f'Unsupported expression: {token}')
            values.append(value & ((1 << (8*width))-1))
    return values


def extract(source, rom):
    header=len(rom)%0x8000
    if header not in (0,512): raise ValueError('Unsupported ROM header')
    checked=[]
    def verify(label,width):
        values=table(source,label,width)
        addr=int(label[5:],16)
        offset=((addr>>16)&0x7F)*0x8000+(addr&0x7FFF)
        raw=b''.join(v.to_bytes(width,'little') for v in values)
        if not raw or rom[header+offset:header+offset+len(raw)]!=raw:
            raise ValueError(f'ROM mismatch: {label}')
        checked.append({'label':label,'lorom_offset':f'{offset:06X}',
                        'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
        return values
    pointers=verify('DATA_819BA7',2)
    modes=[]
    for mode,pointer in enumerate(pointers):
        values=verify(f'DATA_81{pointer:04X}',2)
        if values[-1]!=0 or len(values)%2!=1: raise ValueError('Invalid control terminator')
        records=[]
        for i in range(0,len(values)-1,2):
            first,second=values[i:i+2]
            records.append({'record':f'{0x1AA0+(i//2)*0x30:04X}',
                            'first_word':f'{first:04X}','second_word':f'{second:04X}',
                            'automated_route_bit_8000':bool(first&0x8000),
                            'stored_word_00':first&0x7FFF,
                            'side_bit_0001':not bool(second&0x8000)})
        modes.append({'mode':mode,'table':f'81:{pointer:04X}','records':records})
    directions=verify('DATA_819632',1)
    angular_boundaries=verify('DATA_819491',2)
    # DEB9 indexes eight bytes starting at 9623, crossing the next label.
    selectors=verify('DATA_819623',1)+verify('DATA_819629',1)[:2]
    if len(selectors)!=8: raise ValueError('Unexpected direction selector span')
    strengths=verify('DATA_81DAFE',1)
    speeds=verify('DATA_81A367',1)
    fixed_parameter_paths=[]
    for ball_type,y in ((2,11),(3,11),(29,11)):
        fixed_parameter_paths.append(ball_parameter(ball_type,y,speeds))
    rows=[]
    for direction,(angle,strength) in enumerate(zip(directions,strengths)):
        # 83:94A4 masks to four bits and clamps values >= 12 to 11.
        param=min(strength&15,11)
        rows.append({'native_direction':direction,'angle_0452':angle&63,
                     'parameter_0456':param,'type_0430':7,
                     'table_value_0464':speeds[7*16+param]})
    excerpts=[]
    for start,end in [('838080','8380D9'),('849006','849047'),
                      ('85F3CC','85F3FE'),('85F8C5','85F91D'),
                      ('8394A4','83956E'),('839755','839765'),
                      ('849047','849094'),('84C306','84C328'),
                      ('80F402','80F413'),('80DD9F','80DDB6')]:
        excerpts.append({'label':'CODE_'+start,'assembly_excerpt':source.split(
            'CODE_'+start+':',1)[1].split('CODE_'+end+':',1)[0].strip()})
    return {'schema':'issd-ball-release-and-control-routing/v1',
            'source':str(ASM.relative_to(ROOT)), 'rom_sha256':hashlib.sha256(rom).hexdigest(),
            'verified_tables':checked,'controller_modes':modes,
            'attachment_direction_selectors_819623':selectors,
            'post_release_angular_boundaries_819491':angular_boundaries,
            'fixed_parameter_examples':fixed_parameter_paths,
            'release_F3CC_by_direction':rows,'routines':excerpts,
            'limitations':['Mode numbers are raw; button semantics and sporting action names are not inferred.',
                          '$0464 is a table parameter, not a speed in Canvas units.',
                          '$00A4 records the actor after this release path, not universal ownership.',
                          'Static release proof does not identify exact release frame in old captures.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'dist/data/issd-ball-release.json')
    args=p.parse_args()
    result=extract(ASM.read_text(encoding='utf-8'),args.rom.read_bytes())
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Verified',len(result['verified_tables']),'tables; recovered 9 control modes and 8 release rows')
