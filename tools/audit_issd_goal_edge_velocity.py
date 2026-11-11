"""Check paired native velocity hooks from the isolated goal-edge probe."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
MASK=0xffffffff

def raw(row,axis):return ((row[axis]<<16)|row[axis+'Lo'])
def signed(raw_value):return raw_value-(1<<32) if raw_value & (1<<31) else raw_value

def expected_y(value,direction):
    negative=bool(value & 0x80000000)
    if direction & 0x20:
        return ((-value & MASK)>>2) if negative else value
    return value if negative else (-(value>>2)&MASK)

def expected_x(value):
    negative=bool(value & 0x80000000)
    high=value>>16
    if negative:
        return value if high>=0xfffe else (-((-value & MASK)>>1)&MASK)
    return (value>>1) if high>=2 else value

def audit(path):
    raw_trace=path.read_bytes(); rows=[json.loads(s) for s in raw_trace.splitlines()]
    cases={r['trial']:r for r in rows if r['type']=='case'}
    frames=collections.Counter(r['trial'] for r in rows if r['type']=='frame')
    if len(cases)!=96 or any(frames[i]!=32 for i in range(1,97)): raise ValueError('Incomplete 96-case probe')
    pairs=[]
    for i,r in enumerate(rows[:-1]):
        target={'839073':'8390CB','8390CB':'83A90E'}.get(r.get('pc'))
        if not target:continue
        n=rows[i+1]
        if (n.get('trial'),n.get('step'),n.get('pc'))!=(r['trial'],r['step'],target):continue
        axis='vy' if r['pc']=='839073' else 'vx'
        before=raw(r,axis);after=raw(n,axis)
        expected=expected_y(before,r['direction']) if axis=='vy' else expected_x(before)
        if after!=expected:raise ValueError(f"Mismatch trial {r['trial']} step {r['step']}")
        pairs.append({'trial':r['trial'],'step':r['step'],'axis':axis,'before_signed_fixed':signed(before),'after_signed_fixed':signed(after),'direction':r['direction'],'native_y':r['local2c'],'height_word':r['z']})
    counts=collections.Counter(p['axis'] for p in pairs)
    if counts!={'vx':30,'vy':30}:raise ValueError(f'Unexpected coverage: {counts}')
    entries=collections.Counter(r['pc'] for r in rows if r['type']=='hook')
    return {'schema':'issd-goal-edge-velocity-probe/v1','trace_sha256':hashlib.sha256(raw_trace).hexdigest(),'cases':len(cases),'frames':sum(frames.values()),'entries':dict(sorted(entries.items())),'paired_checks':dict(sorted(counts.items())),'distinct_pairs':sorted([{'axis':axis,'before_signed_fixed':before,'after_signed_fixed':after,'direction':direction,'count':count} for (axis,before,after,direction),count in collections.Counter((p['axis'],p['before_signed_fixed'],p['after_signed_fixed'],p['direction']) for p in pairs).items()],key=lambda x:x['axis']),'pairs':pairs,'limits':['Synthetic states from one saved game; hook pairs are pre-instruction samples in the same frame.','Only the listed observed velocity and direction values were dynamically tested; unexercised branches are static translations.','A response in the edge routine is not by itself proof of post collision; no visual contact or sound was captured.','The height-response branch 838D23 was not observed.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=audit(a.trace);a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8');print('OK:',result['cases'],'cases;',result['paired_checks'])
if __name__=='__main__':main()
