"""Audit player-control records in automated traces; no velocity calibration."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path


def analyze(rows):
    samples=0;groups=defaultdict(Counter);previous=None;last_step=0
    for row in rows:
        if 'step' not in row: continue
        step=row['step']
        if step<=last_step: raise ValueError('Non-monotonic step')
        last_step=step;samples+=1
        name=row['input']; controls=row.get('controls',[])
        controller=next((c for c in controls if c.get('address')==0x1aa0),None)
        if not controller: previous=None;continue
        pointer=controller['actor'];flags=controller['flags']
        actor=next((a for a in row.get('actors',[]) if a.get('address')==pointer),None)
        group=groups[name];group['samples']+=1
        if flags&0x8000: group['automatic_flag_samples']+=1
        if not actor or not actor.get('type'): previous=None;continue
        group['active_actor_samples']+=1
        if pointer!=row.get('selected_p1'):group['pointer_differs_from_1acc']+=1
        if row.get('link_a6') and row['link_a6']!=pointer:group['link_a6_other_actor']+=1
        if controller['held']!=0: group['controller_held_nonzero']+=1
        x=(actor['x']<<16)|actor['x_fraction'];y=(actor['y']<<16)|actor['y_fraction']
        if previous and step-previous['step']==2 and previous['pointer']==pointer and previous['name']==name:
            group['consecutive_pairs']+=1
            if (x,y)!=previous['xy']:group['position_changed_pairs']+=1
        previous={'step':step,'pointer':pointer,'xy':(x,y),'name':name}
    return {'samples':samples,'by_input':{key:dict(value) for key,value in sorted(groups.items())},
            'limitations':['Control record identity follows static 83:8000; it is not alone proof of causality.',
                           '$00A6 is a ball-related link, not a verified universal possession field.',
                           'Changed fixed-point words are not calibrated velocity or Canvas units.',
                           'Samples are two frames apart and game states can include stoppages.']}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('trace',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();digest=hashlib.sha256()
    def rows():
        with a.trace.open('rb') as f:
            for line in f:
                digest.update(line)
                if line.strip(): yield json.loads(line)
    result=analyze(rows());result.update({'schema':'issd-auto-control-summary/v1',
      'source':{'path':a.trace.as_posix(),'bytes':a.trace.stat().st_size,'sha256':digest.hexdigest()}})
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result['by_input'],indent=2))
