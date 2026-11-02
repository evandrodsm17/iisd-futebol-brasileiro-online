"""Compare actor descriptors in one OAM capture with observed charge runs."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(runs, snapshot):
    targets={sample['descriptor'] for run in runs['runs'] for sample in run['samples']
             if isinstance(sample.get('descriptor'),int)}
    actors=snapshot.get('actors',[])
    return {'actors_examined':len(actors), 'target_descriptors':sorted(targets),
            'matches':[{'actor':a.get('object'),'descriptor':a['descriptor'],
                        'direction':a.get('direction'),'parts':len(a.get('parts',[]))}
                       for a in actors if a.get('descriptor') in targets]}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('runs',type=Path)
    p.add_argument('snapshot',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();raw=args.snapshot.read_bytes()
    result=audit(json.loads(args.runs.read_text(encoding='utf-8')),json.loads(raw))
    result.update({'schema':'issd-charge-runtime-snapshot-overlap/v1',
                   'source':{'snapshot':args.snapshot.as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),
                             'runs':args.runs.as_posix()},
                   'limitations':['Descriptor match alone does not establish the same frame or validated OAM grouping.',
                                  'Capture script suggests same-frame files; this export lacks a frame identifier.']})
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'{result["actors_examined"]} actors; {len(result["matches"])} matches')
