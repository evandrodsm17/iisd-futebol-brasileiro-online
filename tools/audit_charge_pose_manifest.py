"""Compare observed descriptor IDs with a user-provided pose audit manifest."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(runs, manifest, asset_root):
    targets={s['descriptor'] for run in runs['runs'] for s in run['samples']
             if isinstance(s.get('descriptor'),int)}
    result={}
    for category in ('rendered','excluded'):
        entries=manifest.get(category,[]); matches=[]
        for item in entries:
            value=item.get('descriptor')
            if not isinstance(value,str): continue
            try: descriptor=int(value.removeprefix('$'),16)
            except ValueError: continue
            if descriptor in targets:
                filename=item.get('filename')
                matches.append({'descriptor':descriptor,'filename':filename,
                                'file_present':bool(filename) and (asset_root/filename).is_file()})
        result[category]={'entries':len(entries),'matches':matches}
    return {'target_descriptors':sorted(targets),'categories':result}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('runs',type=Path)
    p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();raw=args.manifest.read_bytes()
    result=audit(json.loads(args.runs.read_text(encoding='utf-8')),json.loads(raw),args.manifest.parent)
    result.update({'schema':'issd-charge-pose-manifest-overlap/v1',
                   'source':{'runs':args.runs.as_posix(),'manifest':args.manifest.as_posix(),
                             'manifest_sha256':hashlib.sha256(raw).hexdigest()},
                   'limitations':['Descriptor overlap alone does not validate timing, OAM, VRAM or palette.',
                                  'Only the supplied manifest is searched.']})
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print({k:(v['entries'],len(v['matches'])) for k,v in result['categories'].items()})
