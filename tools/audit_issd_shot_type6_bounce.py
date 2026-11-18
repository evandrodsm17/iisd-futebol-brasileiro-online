"""Audit the first type-6 bounce in three natural saved-state replays."""
import argparse
import hashlib
import json
from pathlib import Path


def fixed(e,key):return (e[key]<<16)|e[key+'Frac']


def audit(rom_path,trace_path):
    rom=rom_path.read_bytes()
    checks={0x1895d:'56 36 76 34 60',0x18883:'38 a9 00 00 f5 34 95 34 a9 00 00 f5 36 95 36',
            0x189af:'ad 56 04 4a 8d 56 04 4a 18 6d 56 04 8d 56',
            0x18fdd:'4e 28 04 6e 26 04 ad 28 04 85 00 ad 26 04 85 02 4e 28 04 6e 26 04 18 6d 26 04',
            0x19019:'4e 24 04 6e 22 04 ad 24 04 85 00 ad 22 04 85 02 4e 24 04 6e 22 04 18 6d 22 04'}
    for offset,expected in checks.items():
        if not rom[offset:].startswith(bytes.fromhex(expected)):raise ValueError(f'Unexpected ROM at {offset:x}')
    raw=trace_path.read_bytes();events=[json.loads(s) for s in raw.splitlines()]
    if events[0]!={'type':'session_start','synthetic':False} or events[-1]['type']!='session_end':raise ValueError('Incomplete trace')
    cases=[]
    sites=['83882A','838941','83895D','838866','838883','83898D','8389AF','8388BB']
    for trial,direction in enumerate(('Right','UpRight','DownRight'),1):
        rows=[e for e in events if e.get('trial')==trial]
        cfg=[e for e in rows if e['type']=='case']
        if len(cfg)!=1 or cfg[0]['direction']!=direction or cfg[0]['buttonFrames']!=6:raise ValueError('Unexpected replay')
        vertical=[e for e in rows if e['type']=='vertical']
        impacts=[e for e in vertical if e['site']=='838883']
        if not impacts:raise ValueError('Missing first impact')
        frame=min(e['frame'] for e in impacts)
        selected=[e for e in vertical if e['frame']==frame and e['site'] in sites]
        if [e['site'] for e in selected]!=sites:raise ValueError('Unexpected first impact path')
        start,entry,branch,half,invert,negated,horizontal,done=selected
        if any(e['ballType']!=6 or e['carrier']!=0 or e['x']!=0x400 for e in selected):raise ValueError('Unexpected object')
        if (start['weather'],start['flags'],start['parameter'])!=(1,0,5):raise ValueError('Unexpected contact state')
        value=fixed(entry,'vz');reduced=value>>1
        if value!=(4<<16)+44032 or fixed(half,'vz')!=reduced or fixed(invert,'vz')!=reduced or fixed(negated,'vz')!=(-reduced)&0xffffffff:
            raise ValueError('Vertical response mismatch')
        for axis in ('vx','vy'):
            v=fixed(horizontal,axis);negative=bool(v&0x80000000);mag=(-v)&0xffffffff if negative else v
            reduced=(mag>>1)+(mag>>2);expected=(-reduced)&0xffffffff if negative else reduced
            if fixed(done,axis)!=expected:raise ValueError('Horizontal response mismatch')
        if (done['z'],done['zFrac'],done['parameter'],done['flags'])!=(0,0,3,1):raise ValueError('Unexpected final contact state')
        cases.append({'direction':direction,'frame':frame,'entry':entry,'exit':done})
    return {'schema':'issd-shot-type6-bounce/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':cases,
            'limits':['One saved state, parameter 5, weather 1 and initial flags 0; other impacts are not established.',
                      'Three directions do not establish web input mapping, scaling or all collision behaviour.',
                      'ROM, saved state and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK:',len(report['cases']),'first type-6 bounces verified')
