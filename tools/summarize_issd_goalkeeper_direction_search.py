"""Summarize controlled goalkeeper direction experiments without inferring causality."""
import argparse,hashlib,json
from pathlib import Path
DIRECTIONS={'Up':0x800,'Down':0x400,'Left':0x200,'Right':0x100,'UpLeft':0xa00,'UpRight':0x900,'DownLeft':0x600,'DownRight':0x500}

def scan(path,kind):
    raw=path.read_bytes();rows=[json.loads(x) for x in raw.splitlines() if x.strip()]
    session=next(r for r in rows if r.get('type')=='session_start')
    pre=next(r for r in rows if r.get('type')=='pre_direction')
    second=next((r for r in rows if r.get('type')=='pre_direction2'),None)
    samples={r['step']:r for r in rows if 'step' in r}
    if session['button']!='B' or session['start']!=110 or set(samples)!=set(range(1,181)) or not any(r.get('type')=='session_end' for r in rows):raise ValueError('Incomplete scenario')
    name=path.parent.name
    if kind=='turn' and (not second or second['direction']!=name or pre['direction']!='Up'):raise ValueError('Wrong turn')
    if kind=='long' and (second or pre['direction']!=name):raise ValueError('Wrong direction')
    for t in range(2,110):
        selected=second['direction'] if second and t>=second['start'] else pre['direction']
        if samples[t]['held_p1']!=DIRECTIONS[selected]:raise ValueError(f'Input mismatch at {t}')
    if any(samples[t]['held_p1']!=0x8000 or samples[t]['selected']!=0x500 for t in range(110,116)):raise ValueError('Action input or selection mismatch')
    motion=[r for r in samples.values() if r['script'] in (0xe625,0xe644)]
    if not motion:raise ValueError('No throw script observed')
    groups=[]
    for row in motion:
        k=(row['script'],row['descriptor'],row['direction'])
        if not groups or groups[-1]['key']!=list(k):groups.append({'key':list(k),'first_frame':row['frame'],'count':0})
        groups[-1]['count']+=1
    return {'kind':kind,'direction':name,'sha256':hashlib.sha256(raw).hexdigest(),
            'first_input_direction':pre['direction'],'second_direction':second['direction'] if second else None,
            'switch_step':second['start'] if second else None,'last_pre_action_direction':samples[109]['direction'],
            'action_held_verified':True,'groups':groups}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,default=Path('analysis'));p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 trials=[]
 for dirname,kind in (('keeper-throw-pre110','long'),('keeper-throw-turns','turn')):
  paths=sorted((a.analysis/dirname).glob('*/trial.jsonl'))
  if len(paths)!=8:raise ValueError('Expected eight trials per scenario')
  trials.extend(scan(path,kind) for path in paths)
 result={'schema':'issd-goalkeeper-throw-direction-search/v1','state_sha256':hashlib.sha256(a.state.read_bytes()).hexdigest(),'trials':trials,
 'limitations':['One saved state; not paired controls for each movement.', 'Input observations do not prove general direction mapping or impossibility of other poses.', 'Screen orientation and ball physics require further independent capture.']}
 a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(f'OK: {len(trials)} trials, inputs and sequences recorded')
if __name__=='__main__':main()
