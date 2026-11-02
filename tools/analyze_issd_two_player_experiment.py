"""Summarize a two-controller experiment after its recorded trigger."""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

WINDOWS=((0,60,'neutral_before'),(60,180,'p1_right'),(180,240,'neutral_between'),
         (240,360,'p2_right'),(360,420,'neutral_after'),(420,426,'p1_a'),
         (480,486,'p2_a'))


def analyze(rows):
    trigger=None;end=None;last=0;counts=Counter();pairs=Counter();prev={};ball={}
    for row in rows:
        if row.get('type')=='experiment_start':
            if trigger is not None: raise ValueError('Duplicate trigger')
            trigger=row['step'];continue
        if row.get('type')=='session_end': end=row;continue
        if row.get('type') or 'step' not in row:continue
        step=row['step']
        if step<=last:raise ValueError('Non-monotonic step')
        last=step
        if trigger is None:continue
        elapsed=step-trigger
        window=next((label for lo,hi,label in WINDOWS if lo<=elapsed<hi),None)
        if window is None:continue
        counts[window]+=1
        ball.setdefault(window,[]).append([row['ball'][k] for k in ('x','y','z')])
        for port,record in ((1,0x1aa0),(2,0x1ad0)):
            control=next((c for c in row.get('controls',[]) if c['address']==record),None)
            if not control:continue
            actor=next((a for a in row.get('actors',[]) if a['address']==control['actor'] and a['type']),None)
            if not actor:prev.pop(port,None);continue
            key=f'{window}_p{port}'
            if control['held']:pairs[(key,'held_nonzero')]+=1
            x=(actor['x']<<16)|actor['x_fraction'];y=(actor['y']<<16)|actor['y_fraction']
            old=prev.get(port)
            if old and old['step']+2==step and old['address']==actor['address'] and old['window']==window:
                pairs[(key,'pairs')]+=1
                if (x,y)!=old['xy']:pairs[(key,'changed')]+=1
            prev[port]={'step':step,'address':actor['address'],'window':window,'xy':(x,y)}
    return {'trigger_step':trigger,'completed':bool(end),'samples_by_window':dict(counts),
            'actors':{k:{kind:n for (key,kind),n in pairs.items() if key==k}
                      for k in sorted({key for key,_ in pairs})},
            'ball_observed':{k:{'first':v[0],'last':v[-1],'distinct_positions':len({tuple(p) for p in v})}
                             for k,v in ball.items()},
            'limitations':['Trigger is a heuristic, not proof of active gameplay.',
                           'Two-frame samples do not prove exact timing or action semantics.',
                           'No reset baseline, causal speed attribution, or unit conversion.',
                           'A button input is not proof of a pass or shot.']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();digest=hashlib.sha256()
    def rows():
        with a.trace.open('rb') as f:
            for line in f:
                digest.update(line)
                if line.strip():yield json.loads(line)
    result=analyze(rows());result.update({'schema':'issd-two-player-experiment/v1',
        'source':{'path':a.trace.as_posix(),'sha256':digest.hexdigest(),'bytes':a.trace.stat().st_size}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'trigger_step':result['trigger_step'],'samples':result['samples_by_window'],
                      'actors':result['actors']},indent=2))
