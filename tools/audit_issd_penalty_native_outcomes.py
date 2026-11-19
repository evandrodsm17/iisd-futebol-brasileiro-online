"""Join native shot launch, crossing, deferred checks and score snapshots."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_issd_penalty_goal_geometry import model as geometry
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path,trace_path,shots_path,deferred_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    code=bytes.fromhex('a5 0c c9 5c 00 b0 e2 ad aa 14 a6 08 e0 18 00 90 37 a6 08 e0 e0 00 b0 30 a6 0c e0 60 00 b0 29 a6 10 10 05 e0 b8 ff 90 20 22 d2 9c 8c')
    if rom[0x60d79:0x60d79+len(code)]!=code:raise ValueError('Unexpected native goal geometry')
    raw=trace_path.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    shots_raw=shots_path.read_bytes();shots=json.loads(shots_raw)
    deferred_raw=deferred_path.read_bytes();deferred=json.loads(deferred_raw)
    if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end' or shots['schema']!='issd-penalty-shot-chain/v1' or shots['trace_sha256']!=hashlib.sha256(raw).hexdigest() or deferred['schema']!='issd-penalty-deferred-checks/v1':raise ValueError('Invalid source reports')
    results=[]
    for shot in shots['shots']:
        found=[e for e in events if e.get('site')=='penalty_crossing_resolved' and (e['frame'],e['side'],e['round'])==(shot['resolved_frame'],shot['side'],shot['round'])]
        if len(found)!=1:raise ValueError('Missing unique crossing')
        crossing=found[0]
        if [crossing['x_coord'],crossing['y_coord'],crossing['height']]!=shot['final_native_position'] or [crossing['penalty_home'],crossing['penalty_away']]!=shot['score']:raise ValueError('Crossing context mismatch')
        if shot['resolution']=='goal_branch':
            if geometry(crossing) is not True:raise ValueError('Goal does not match native geometry')
            reason='goal_branch'
        elif shot['resolution']=='deferred':
            matching=[c for c in deferred['cases'] if c['resolved_frame']==crossing['frame']]
            if len(matching)!=1 or matching[0]['resolved_flags']!=crossing['shot_flags'] or matching[0]['initial_score']!=shot['score']:raise ValueError('Deferred resolution mismatch')
            reason='deferred'
        else:raise ValueError('Unexpected resolution route')
        results.append({'launch_frame':shot['frame'],'resolved_frame':crossing['frame'],'side':shot['side'],
                        'input_word':shot['input_word'],'launch_flags':shot['flags'],'resolution_flags':crossing['shot_flags'],
                        'position':{'x':crossing['x_coord'],'y':crossing['y_coord'],'height':crossing['height']},
                        'reason':reason,'score':shot['score']})
    if len(results)!=8 or sum(e['reason']=='deferred' for e in results)!=2:raise ValueError('Unexpected observed outcomes')
    return {'schema':'issd-penalty-native-outcomes/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'shots_sha256':hashlib.sha256(shots_raw).hexdigest(),'deferred_sha256':hashlib.sha256(deferred_raw).hexdigest(),
            'cases':results,'limits':['Eight shots from a synthetic shootout and a separately instrumented replay.',
            'Native coordinates, words and shot timing have not been mapped to the web scene.',
            'Deferred resolution bypasses the direct geometry test in this observed path; other routes remain unverified.',
            'ROM and raw traces remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','shots','deferred','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.trace,args.shots,args.deferred)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK: 8 captured native outcomes, including 2 deferred')
