"""Compare isolated FAEA execution with the existing native word model."""
import argparse
import hashlib
import json
from pathlib import Path
from issd_contact_volume import contact_volume


def audit(paths):
    samples=[];sources=[]
    for path in paths:
        raw=path.read_bytes();sources.append({'sha256':hashlib.sha256(raw).hexdigest()})
        for line in raw.splitlines():
            if not line.strip():continue
            row=json.loads(line)
            if row['carry'] not in (0,1):raise ValueError('CPU carry unavailable')
            expected=contact_volume([12,24,8,16,8,16],row['actor_xyz'],row['offset_xyz'],row['ball_xyz'],
                                    phase=row['phase'],flag_11fa=row['global'],actor_flags=row['flags'])
            if row['carry']!=expected['carry'] or row['flags_after']!=expected['actor_flags']:
                raise ValueError(f"Gate mismatch at frame {row['frame']}")
            samples.append({'frame':row['frame'],'script':f"${row['script']:04X}",'synthetic':row.get('synthetic',False),
                            'carry':row['carry'],'rejected_by':expected['rejected_by']})
    if not any(x['carry']==1 and not x['synthetic'] for x in samples) or not any(x['carry']==0 and x['synthetic'] for x in samples):raise ValueError('Need natural outside and synthetic contact observations')
    return {'schema':'issd-slide-ball-gate-probe/v1','sources':sources,'samples':samples,
            'limitations':['Shared FAEA gate was observed under script $DF7F, not under slide $DB25.',
                           'The successful contact was induced by temporarily changing ball coordinates in isolated RAM.',
                           'Does not validate the slide timing, entry button, collision response, foul or browser mapping.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('captures',nargs='+',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.captures);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print(f"Validated {len(r['samples'])} shared-gate observations")
