"""Audit a completed isolated BizHawk goal-boundary probe (no ROM redistribution)."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

def audit(path):
    raw=path.read_bytes()
    records=[json.loads(line) for line in raw.splitlines()]
    cases={r['trial']:r for r in records if r['type']=='case'}
    frames=collections.Counter(r['trial'] for r in records if r['type']=='frame')
    if len(cases)!=72 or any(frames[i]!=24 for i in range(1,73)):
        raise ValueError('Expected 72 complete cases of 24 frames')
    counts=collections.Counter()
    seen=collections.defaultdict(set)
    for i,r in enumerate(records):
        if r.get('type')!='hook': continue
        seen[r['trial']].add(r['pc'])
        if r['pc']!='838BAB': continue
        if r['regX']!=0x400 or (r['bandLow'],r['bandHigh'])!=(264,376):
            raise ValueError('Unexpected actor or stadium thresholds')
        y=r['local2c']
        branch='outer' if y<264 or y>=376 else 'edge' if y<272 or y>=368 else 'inner'
        expected={'outer':'838DDC','edge':'838BC8','inner':'838D76'}[branch]
        next_record=records[i+1]
        if (next_record.get('trial'),next_record.get('step'),next_record.get('pc'))!=(r['trial'],r['step'],expected):
            raise ValueError(f"Unexpected branch in trial {r['trial']} step {r['step']}")
        counts[branch]+=1
    if not all(counts[k] for k in ('outer','edge','inner')):
        raise ValueError('Probe did not cover all three branches')
    per_side={}
    for side in (-1,1):
        selected=[trial for trial,c in cases.items() if c['side']==side]
        per_side[str(side)]={'cases':len(selected),'cases_with_band_entry':sum('838BAB' in seen[t] for t in selected),'cases_with_86d98c':sum('86D98C' in seen[t] for t in selected)}
    return {'schema':'issd-goal-boundary-probe/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':len(cases),'frames':sum(frames.values()),'stadium_indices':sorted({c['stadium'] for c in cases.values()}),'branch_entries':dict(sorted(counts.items())),'per_side':per_side,'case_parameters':{'offsets':sorted({c['offset'] for c in cases.values()}),'heights':sorted({c['height'] for c in cases.values()}),'sides':[-1,1]},'scope':['Synthetic ball states restored from one gameplay save; RAM injected in isolated emulator.','Branches matched by comparing actual local2c at hook entry, not requested offset.','Hooks prove control flow only; score, post contact, visual geometry and natural shots are not established.','The horizontal and vertical motion can change before reaching the boundary; some cases never enter the band routine.']}

def main():
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    result=audit(args.trace);args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
    print('OK:',result['cases'],'cases,',result['frames'],'frames; branches',result['branch_entries'])
if __name__=='__main__': main()
