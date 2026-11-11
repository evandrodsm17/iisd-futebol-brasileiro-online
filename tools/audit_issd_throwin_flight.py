"""Audit vertical throw-in flight and recorded first impacts from local replays."""
import argparse
import hashlib
import json
from pathlib import Path

CASES=('upper-A-Down','upper-A-Up','upper-B-Down','upper-B-Up','lower-A-Left','lower-B-Right')
MASK=0xffffffff


def value(ball, key):
    return (ball[key] << 16) | ball[key+'_fraction']


def audit(root):
    result=[]
    for case in CASES:
        path=root/case/'trace.jsonl';raw=path.read_bytes()
        rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        if rows[-1].get('type')!='done':raise ValueError(f'Incomplete replay {case}')
        samples={r['step']:r for r in rows if 'step' in r}
        if set(samples)!=set(range(400)):raise ValueError(f'Missing or duplicate samples {case}')
        ball_type=20 if '-A-' in case else 15
        if samples[70]['ball']['type']!=ball_type or samples[70]['a6']!=0:raise ValueError(f'No expected release {case}')
        transitions=0;impact=None;end=None
        for tick in range(70,399):
            before,after=samples[tick]['ball'],samples[tick+1]['ball']
            if before['type']!=ball_type or after['type']!=ball_type:
                end={'step':tick+1,'type':after['type'],'link_a6':samples[tick+1]['a6']};break
            z0,z1=value(before,'z'),value(after,'z');v0,v1=value(before,'vz'),value(after,'vz')
            if v1==(v0+0x2000)&MASK and z1==(z0+v1)&MASK:
                transitions+=1;continue
            impact={'step':tick+1,'before_z':z0,'before_vz':v0,'after_z':z1,'after_vz':v1};break
        if transitions<20:raise ValueError(f'Insufficient continuous flight evidence {case}')
        result.append({'case':case,'airborne_transitions':transitions,'first_nonflight':impact or end,
                       'trace_sha256':hashlib.sha256(raw).hexdigest()})
    by={x['case']:x for x in result}
    expected={'upper-A-Up':(121,0xffff8000,0x0003a000,0,0xfffe2000),
              'upper-B-Down':(105,0x00004000,0x0002e000,0,0xfffe8000),
              'upper-B-Up':(105,0x00004000,0x0002e000,0,0xfffe8000)}
    for name,values in expected.items():
        item=by[name]['first_nonflight']
        if tuple(item.get(k) for k in ('step','before_z','before_vz','after_z','after_vz'))!=values:
            raise ValueError(f'Impact mismatch {name}')
    return {'schema':'issd-throwin-flight-audit/v1','cases':result,
            'limitations':['One original upper restart and one synthetic lower restart.',
                           'Links after flight are observations and do not alone establish possession.',
                           'No conversion to browser coordinates; only two exact vertical impact states reproduced.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();r=audit(a.root);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('Validated six captured flight traces and three observed impacts')
