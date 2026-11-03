"""Compare observed action descriptors to direction lists in the corrected tables."""
import argparse
import hashlib
import json
from collections import Counter,defaultdict
from pathlib import Path


def audit(trace,manifest):
    data=json.loads(manifest.read_text(encoding='utf-8'))
    names={'$82:D007':'big_kick','$82:D100':'big_kick_alternate','$82:D79B':'turn_while_sprinting'}
    tables={int(script.split(':')[1],16):data['actions'][name]['directions'] for script,name in names.items()}
    counts=Counter();unique=defaultdict(set);examples=[];digest=hashlib.sha256()
    with trace.open('rb') as src:
        for line in src:
            digest.update(line)
            if not line.strip():continue
            row=json.loads(line)
            for actor in row.get('actors',[]):
                script=actor.get('animation_script');direction=actor.get('direction');descriptor=actor.get('descriptor')
                if script not in tables or not isinstance(direction,int) or not 0<=direction<8 or not isinstance(descriptor,int):continue
                valid=descriptor in tables[script][direction]['descriptors']
                counts[(script,valid)]+=1;unique[(script,direction)].add(descriptor)
                if not valid and len(examples)<20: examples.append({'frame':row.get('frame'),'script':script,'direction':direction,'descriptor':descriptor})
    return {'schema':'issd-action-table-coverage/v1','trace_sha256':digest.hexdigest(),
            'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),
            'scripts':[{'script':script,'matching_samples':counts[(script,True)],'nonmatching_samples':counts[(script,False)],
                        'observed':{str(d):sorted(unique[(script,d)]) for d in range(8) if unique[(script,d)]}}
                       for script in tables], 'nonmatching_examples':examples,
            'limitations':['Samples are observations, not independent complete animation executions.',
                           'Matching descriptor does not prove duration, geometry, palette, or action semantics.',
                           'The native trace samples alternate frames and may omit poses.',
                           'Static timing can vary by calling path and be interrupted by gameplay.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('trace',type=Path);p.add_argument('manifest',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.trace,a.manifest);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('samples:',sum(x['matching_samples'] for x in r['scripts']),'nonmatching:',sum(x['nonmatching_samples'] for x in r['scripts']))
