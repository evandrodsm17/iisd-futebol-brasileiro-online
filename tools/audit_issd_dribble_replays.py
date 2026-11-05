"""Measure native actor/ball offsets during controlled replay input."""
import argparse
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

INPUTS = {'Up','UpRight','Right','DownRight','Down','DownLeft','Left','UpLeft'}


def signed_delta(a,b):
    return ((a-b+0x8000)&0xffff)-0x8000


def percentile(values, fraction):
    values=sorted(values)
    return round(values[round((len(values)-1)*fraction)],3) if values else None


def audit(paths, actor=0x1900):
    grouped=defaultdict(list);sources=[];rejected=0
    for path in paths:
        raw=path.read_bytes()
        try: source=path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except ValueError: source=path.name
        sources.append({'file':source,'sha256':hashlib.sha256(raw).hexdigest()})
        for line in raw.splitlines():
            row=json.loads(line)
            direction=row.get('input_p2');ball=row.get('ball') or {}
            if direction not in INPUTS or row.get('link_a6')!=actor or ball.get('z')!=0:continue
            controls=row.get('controls') or []
            if len(controls)<2 or controls[1].get('actor')!=actor:rejected+=1;continue
            matches=[a for a in row.get('actors',[]) if a.get('address')==actor]
            if len(matches)!=1:rejected+=1;continue
            player=matches[0]
            if any(not isinstance(value,int) or not 0<=value<=0xffff for value in (ball.get('x'),ball.get('y'),player.get('x'),player.get('y'))):rejected+=1;continue
            dx=signed_delta(ball['x'],player['x']);dy=signed_delta(ball['y'],player['y'])
            grouped[direction].append((dx,dy,math.hypot(dx,dy)))
    return {'schema':'issd-dribble-replay-offsets/v1','actor':actor,'sources':sources,'rejected_samples':rejected,
            'directions':{name:{'samples':len(v),'distance_p10':percentile([x[2] for x in v],.1),'distance_median':percentile([x[2] for x in v],.5),'distance_p90':percentile([x[2] for x in v],.9),'x_min':min(x[0] for x in v),'x_max':max(x[0] for x in v),'y_min':min(x[1] for x in v),'y_max':max(x[1] for x in v)} for name,v in sorted(grouped.items())},
            'limitations':['Raw integer positions, sampled at trace cadence; fractional positions and full possession semantics are not established.', 'Input labels do not prove running versus walking; includes transitions.', 'Native axes and units are not calibrated to browser coordinates.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('traces',type=Path,nargs='+');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.write_text(json.dumps(audit(a.traces),indent=2)+'\n',encoding='utf8')
