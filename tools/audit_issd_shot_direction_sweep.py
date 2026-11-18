"""Audit naturally generated direction inputs in a fixed pre-shot replay."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, trace_path):
    rom=rom_path.read_bytes()
    checks={0x2f6be:'a5 40 4a 90 1a',0x6833:'85 40 ad d8 12 18 65 40 8d b0 00 6b'}
    for offset,expected in checks.items():
        if not rom[offset:].startswith(bytes.fromhex(expected)):
            raise ValueError(f'Unexpected ROM bytes at {offset:x}')
    raw=trace_path.read_bytes()
    events=[json.loads(line) for line in raw.splitlines()]
    if events[0]!={'type':'session_start','synthetic':False} or events[-1]['type']!='session_end':
        raise ValueError('Incomplete or synthetic trace')
    directions=['neutral','up','down','left','right','up_left','up_right','down_left','down_right']
    held_masks=[0,0x800,0x400,0x200,0x100,0xa00,0x900,0x600,0x500]
    cases=[]
    for trial in range(1,19):
        rows=[e for e in events if e.get('trial')==trial]
        cfg=[e for e in rows if e['type']=='case']
        expected_direction=directions[(trial-1)%9]
        if len(cfg)!=1 or cfg[0]['direction']!=expected_direction or cfg[0]['holdDirection']!=(trial>9) or cfg[0]['heldFrames']!=6:
            raise ValueError('Unexpected input plan')
        def one(site):
            matches=[e for e in rows if e['type']=='hook' and e['site']==site]
            if len(matches)!=1:raise ValueError(f'Unexpected {site} count in trial {trial}')
            return matches[0]
        post=one('85F6BE')
        if post['held'] != (held_masks[(trial-1)%9] if trial>9 else 0):
            raise ValueError('Unexpected controller input at release')
        helper=[e for e in rows if e['type']=='hook' and e['site']=='80E833' and e['frame']==post['frame']]
        if len(helper)!=1 or helper[0]['a']!=post['actor40'] or not post['flags']&0x800:
            raise ValueError('Unexpected post-helper value or flag')
        release=one('85F89B')
        expected_type=6 if post['actor40']&1 else 5
        if release['x']!=expected_type or release['y']!=release['charge']:
            raise ValueError('Unexpected release selection')
        free=[e for e in rows if e['type']=='frame' and e['step']>=release['step'] and e['carrier']==0 and e['ballType']==expected_type]
        if not free:raise ValueError('Selected type not observed after release')
        cases.append({'direction':expected_direction,'hold_direction_after_button':cfg[0]['holdDirection'],
                      'post_helper_word':post['actor40'],'helper_index':helper[0]['y'],
                      'held_at_release':post['held'],'release_flags':post['flags'],'ball_type':expected_type,'parameter':release['y'],
                      'release_step':release['step'],'free_ball_step':min(e['step'] for e in free)})
    if [c['direction'] for c in cases if c['ball_type']==6] != ['right','up_right','down_right']:
        raise ValueError('Unexpected type-6 coverage')
    return {'schema':'issd-shot-direction-sweep/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':cases,
            'limitations':['One actor, saved state and button duration; this is not a universal input-to-shot mapping.',
                           'The tested direction is native controller input, not automatically a browser key mapping.',
                           'ROM, saved state and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK:',len(report['cases']),'direction cases, including three natural type-6 releases')
