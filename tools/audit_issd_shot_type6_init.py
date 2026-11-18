"""Validate type-6 initialization against ROM tables and natural replays."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_issd_shot_direction_sweep import audit as audit_sweep


def word(rom,offset):return int.from_bytes(rom[offset:offset+2],'little')


def audit(rom_path,trace_path):
    rom=rom_path.read_bytes()
    if not rom[0x195d0:].startswith(bytes.fromhex('20 40 96 b9 bf 9e 95 36 b9 d7 9e 95 34 b9 ef 9e 95 58 22 04 96 83 6b')):
        raise ValueError('Unexpected type-6 initializer')
    sweep=audit_sweep(rom_path,trace_path)
    raw=trace_path.read_bytes()
    events=[json.loads(line) for line in raw.splitlines()]
    observed=[]
    for trial in (14,16,18):
        rows=[e for e in events if e.get('trial')==trial]
        before=[e for e in rows if e.get('type')=='ball_init' and e.get('site')=='8395D0']
        after=[e for e in rows if e.get('type')=='ball_init' and e.get('site')=='8395E6']
        if len(before)!=1 or len(after)!=1 or before[0]['frame']!=after[0]['frame']:
            raise ValueError('Missing initializer hooks')
        e=after[0];index=min(e['parameter'],11)*2
        if e['ballType']!=6 or (e['vz'],e['vzFrac'],e['gravity'])!=(word(rom,0x9ebf+index),word(rom,0x9ed7+index),word(rom,0x9eef+index)):
            raise ValueError('Type-6 values differ from ROM tables')
        case=sweep['cases'][trial-1]
        if case['ball_type']!=6 or case['parameter']!=e['parameter'] or case['release_step']!=e['step']:
            raise ValueError('Initializer is not linked to the release')
        observed.append({'direction':case['direction'],'parameter':e['parameter'],'frame':e['frame'],
                         'vz':e['vz'],'vz_fraction':e['vzFrac'],'gravity':e['gravity']})
    ref=[e for e in events if e.get('trial')==1 and e.get('type')=='frame' and e['step']==10]
    if len(ref)!=1 or ref[0]['ballType']!=5 or ref[0]['charge']!=5:
        raise ValueError('Missing comparison sample')
    return {'schema':'issd-shot-type6-init/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'cases':observed,'type5_frame_sample':{'vz':ref[0]['vz'],'vz_fraction':ref[0]['vzFrac'],'gravity':ref[0]['gravity']},
            'limitations':['Three directions from one saved state with parameter 5; other parameters are statically translated, not captured.',
                           'The type-5 comparison is an end-of-frame sample; the type-6 value is at the initializer hook.',
                           'No conversion to browser units or complete trajectory and collision model is established.',
                           'ROM, saved state and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK:',len(report['cases']),'natural type-6 initializations verified')
