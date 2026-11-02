"""Find descriptor overlap between observed runs and separately captured OAM dumps."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(runs, records, directory):
    targets={sample['descriptor'] for run in runs['runs'] for sample in run['samples']
             if isinstance(sample.get('descriptor'),int)}
    matches=[]; count=0
    for record in records:
        count+=1; actor=record.get('actor') or {}
        if actor.get('descriptor') not in targets: continue
        files={key:bool(record.get(key)) and (directory/record[key]).is_file()
               for key in ('vram','cgram','oam_mirror','screenshot')}
        matches.append({'frame':record.get('frame'),'actor':actor.get('address'),
                        'descriptor':actor.get('descriptor'),'script':actor.get('animation_script'),
                        'files_present':files})
    return {'target_descriptors':sorted(targets),'snapshots_examined':count,'matches':matches,
            'limitations':['Matching descriptor is not proof of same frame, actor, palette or complete OAM composition.',
                           'Missing overlap does not prove graphics are absent from other captures.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('runs',type=Path);p.add_argument('snapshots',type=Path)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    runs=json.loads(args.runs.read_text(encoding='utf-8'))
    raw=args.snapshots.read_bytes()
    records=(json.loads(line) for line in raw.splitlines() if line.strip())
    result=audit(runs,records,args.snapshots.parent)
    result.update({'schema':'issd-charge-graphics-overlap/v1',
                   'source':{'runs':args.runs.as_posix(),'snapshots':args.snapshots.as_posix(),
                             'snapshots_sha256':hashlib.sha256(raw).hexdigest()}})
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'{result["snapshots_examined"]} snapshots, {len(result["matches"])} descriptor matches')
