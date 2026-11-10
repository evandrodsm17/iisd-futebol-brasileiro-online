"""Audit already recorded no-D-pad X-button releases in isolated replays."""
import argparse
import hashlib
import json
from pathlib import Path

CASES=[('right','shot-body-replay',0),('up','shot-facing-Up',6),('down','shot-facing-Down',2),
       ('down_right','shot-facing-DownRight',1),('left','shot-facing-Left',4),
       ('up_right','shot-pre-UpRight',7),('up_left','shot-search-UpLeft-380',5),
       ('down_left','shot-search-DownLeft-380',3)]


def signed(value):return value if value<0x8000 else value-0x10000


def audit(root):
    cases={}
    for name,folder,direction in CASES:
        paths=[x for x in (root/folder).glob('issd-auto-probe-*.jsonl') if not x.name.endswith('-graphics.jsonl')]
        if len(paths)!=1:raise ValueError(f'Expected one trace for {name}')
        raw=paths[0].read_bytes();rows=[json.loads(line) for line in raw.splitlines() if line.strip()]
        shots=[]
        for row in rows:
            actors=[a for a in row.get('actors',[]) if a.get('address')==0x1900]
            if len(actors)==1 and row.get('input_p2')=='X' and row.get('held_p2')==0x40 and row.get('link_a6')==0x1900 and actors[0].get('script')==0xd007 and actors[0].get('direction')==direction:
                shots.append(row)
        if not shots:raise ValueError(f'Missing directed actor and X-only input for {name}')
        start=shots[0]['step'];releases=[r for r in rows if isinstance(r.get('step'),int) and start<=r['step']<=start+20 and r.get('link_a6')==0 and r.get('ball',{}).get('type') in (3,5)]
        if not releases:raise ValueError(f'Missing release for {name}')
        release=releases[0];ball=release['ball'];actor=next(a for a in release['actors'] if a['address']==0x1900)
        if actor['script']!=0xd007 or actor['direction']!=direction:raise ValueError(f'Animation changed before release: {name}')
        cases[name]={'trace_sha256':hashlib.sha256(raw).hexdigest(),'input_step':start,'native_direction':direction,'release_step':release['step'],'ball_type':ball['type'],'ball_velocity_words':{'x':signed(ball['vx']),'y':signed(ball['vy']),'z':signed(ball['vz'])}}
    return {'schema':'issd-shot-facing-replays/v1','cases':cases,'limitations':['One actor, saved state and command per direction; traces do not prove all native input contexts.','Velocity words use native world axes; they are not calibrated Canvas velocities.','Some releases occur after X is released; no D-pad was pressed with X in these samples.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.write_text(json.dumps(audit(a.root),indent=2)+'\n',encoding='utf8')
