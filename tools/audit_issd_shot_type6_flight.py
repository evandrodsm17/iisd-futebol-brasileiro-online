"""Verify type-6 airborne integration before first observed ground impact."""
import argparse
import hashlib
import json
from pathlib import Path


def fixed(row,name):return (row[name]<<16)|row[name+'Frac']


def audit(rom_path,trace_path):
    rom=rom_path.read_bytes()
    for offset,expected in ((0x1882a,'18 b5 0e 75 34 95 0e b5 10 75 36'),(0x18863,'95 10 60'),(0x1942e,'b5 58 18 75 34 95 34 b5 36 69 00 00 95 36 60')):
        if not rom[offset:].startswith(bytes.fromhex(expected)):raise ValueError('Unexpected airborne instruction')
    raw=trace_path.read_bytes()
    events=[json.loads(line) for line in raw.splitlines()]
    if events[0]!={'type':'session_start','synthetic':False} or events[-1]['type']!='session_end':raise ValueError('Incomplete trace')
    cases=[]
    for trial,direction in enumerate(('Right','UpRight','DownRight'),1):
        rows=[e for e in events if e.get('trial')==trial]
        cfg=[e for e in rows if e['type']=='case']
        if len(cfg)!=1 or cfg[0]['direction']!=direction or cfg[0]['buttonFrames']!=6:raise ValueError('Unexpected input case')
        vertical=[e for e in rows if e['type']=='vertical']
        impacts=[e for e in vertical if e['site']=='838883']
        if not impacts:raise ValueError('No observed bounce')
        first_impact=min(e['frame'] for e in impacts)
        grouped={}
        for e in vertical:
            if e['frame']<first_impact:grouped.setdefault(e['frame'],[]).append(e)
        verified=[]
        for frame,group in sorted(grouped.items()):
            if [e['site'] for e in group] != ['83941F','83942E','83882A','838863','838865']:
                raise ValueError(f'Unexpected airborne hook sequence in frame {frame}')
            entry,accel,before,store,after=group
            if any(e['ballType']!=6 or e['carrier']!=0 or e['x']!=0x400 for e in group):raise ValueError('Unexpected ball context')
            velocity=(fixed(accel,'vz')+accel['gravity'])&0xffffffff
            position=(fixed(before,'z')+velocity)&0xffffffff
            if fixed(before,'vz')!=velocity or store['a']!=position>>16 or fixed(after,'z')!=position or not position&0x80000000:
                raise ValueError('Airborne integration mismatch')
            verified.append({'frame':frame,'position_before':fixed(accel,'z'),'velocity_before':fixed(accel,'vz'),
                             'gravity':accel['gravity'],'velocity_after':velocity,'position_after':position})
        if not verified:raise ValueError('No verified steps')
        cases.append({'direction':direction,'first_impact_frame':first_impact,'steps':verified})
    return {'schema':'issd-shot-type6-flight/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':cases,
            'limitations':['One actor and saved state; three directions share the same parameter.',
                           'Only the airborne path before the first impact is verified; collisions and bounce remain separate.',
                           'Native units are not calibrated to the browser.', 'ROM, saved state and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK:',sum(len(c['steps']) for c in report['cases']),'type-6 airborne updates before first impact')
