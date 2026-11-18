"""Audit isolated shot branches with explicitly recorded RAM interventions."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, trace_path):
    rom=rom_path.read_bytes()
    checks={0x6770:'a9 00 08 14 6e a5 6e 4a a5 2a b0 07 cd f2 12 10 07 18 6b cd f2 12 10 f9 a9 00 08 04 6e 38 6b',
            0x2f6be:'a5 40 4a 90 1a', 0x2f6d5:'a2 06 00 a4 82 4c 9b f8'}
    for offset,expected in checks.items():
        if not rom[offset:].startswith(bytes.fromhex(expected)):
            raise ValueError(f'Unexpected ROM at {offset:x}')
    raw=trace_path.read_bytes()
    events=[json.loads(line) for line in raw.splitlines()]
    if events[0] != {'type':'session_start','synthetic':True} or events[-1]['type']!='session_end':
        raise ValueError('Incomplete synthetic trace')
    result=[]
    for trial,scenario,expected_type in [(1,'control',5),(2,'opposite_field',3),(3,'odd_helper',6)]:
        rows=[e for e in events if e.get('trial')==trial]
        cases=[e for e in rows if e['type']=='case']
        if len(cases)!=1 or cases[0]['scenario']!=scenario:
            raise ValueError('Unexpected case')
        interventions=[e for e in rows if e['type']=='intervention']
        if scenario=='control':
            if interventions:raise ValueError('Control was modified')
        elif len(interventions)!=1 or interventions[0]['field']!=('actor2a' if scenario=='opposite_field' else 'actor40'):
            raise ValueError('Unexpected intervention')
        def hook(name):
            matches=[e for e in rows if e['type']=='hook' and e['site']==name]
            if len(matches)!=1:raise ValueError(f'Expected one {name} in {scenario}')
            return matches[0]
        entry=hook('80E770')
        branch=hook('80E781' if scenario=='opposite_field' else '80E788')
        release_entry=hook('85F694')
        release=hook('85F871' if expected_type==3 else '85F89B')
        negative=bool(((entry['actor2a']-entry['middle']) & 0xffff) & 0x8000)
        set_flag=negative if entry['flags']&1 else not negative
        if set_flag != (scenario!='opposite_field') or bool(release_entry['flags']&0x800)!=set_flag:
            raise ValueError('Field branch mismatch')
        if release['x']!=expected_type or release['y']!=(11 if expected_type==3 else release['charge']):
            raise ValueError('Release mismatch')
        post_helper=None
        if expected_type!=3:
            post_helper=hook('85F6BE')['actor40']
            if (post_helper&1)!=(expected_type==6):raise ValueError('Helper branch mismatch')
        frames=[e for e in rows if e['type']=='frame' and e['step']>=release['step'] and e['carrier']==0 and e['ballType']==expected_type]
        if not frames:raise ValueError('Selected type not seen in free ball')
        result.append({'scenario':scenario,'intervention':interventions[0] if interventions else None,
                       'flags_before':entry['flags'],'actor_coordinate':entry['actor2a'],'boundary':entry['middle'],
                       'branch_set':set_flag,'branch_site':branch['site'],'release_flags':release_entry['flags'],
                       'post_helper_word':post_helper,'charge':release['charge'],'ball_type':expected_type,
                       'parameter':release['y'],'release_step':release['step'],'free_ball_step':min(e['step'] for e in frames)})
    return {'schema':'issd-shot-synthetic-branches/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':result,
            'limitations':['One saved state; opposite-field and odd-helper values are explicit isolated RAM interventions.',
                           'These tests do not establish that the modified states occur naturally or how controls reach them.',
                           'ROM, savestate and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK: control and two explicitly synthetic branches verified')
