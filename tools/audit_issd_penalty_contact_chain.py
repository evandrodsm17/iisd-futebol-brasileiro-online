"""Join captured penalty collision checks to the following contact response."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_issd_penalty_hitboxes import collision
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path,trace_path,response_path,response_trace_path,asset_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    gate=bytes.fromhex('ad aa 14 89 60 00 d0 5a 0b a5 36 5b a6 14 bf 6c bc 8c a8 a6 1a 20 75 a3 90 28 ad aa 14 89 00 01 f0 14 ad 06 17 c9 01 00 f0 0c c9 02 00 f0 07 c9 03 00 f0 02 80 0c')
    if rom[0x614c6:0x614c6+len(gate)]!=gate or rom[0x6150a:0x6151b]!=bytes.fromhex('ad aa 14 89 20 00 d0 16 a9 00 08 0c aa 14 a9 00 01'):
        raise ValueError('Unexpected native gates')
    raw=trace_path.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    response_raw=response_path.read_bytes();response=json.loads(response_raw)
    response_trace_raw=response_trace_path.read_bytes();response_events=[json.loads(line) for line in response_trace_raw.splitlines()]
    if hashlib.sha256(response_trace_raw).hexdigest()!=response.get('trace_sha256'):raise ValueError('Mismatched response trace')
    asset_raw=asset_path.read_bytes();asset=json.loads(asset_raw)
    if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end' or response['schema']!='issd-penalty-contact-response/v1' or asset['schema']!='issd-penalty-hitbox-tables/v1':raise ValueError('Invalid source')
    cases=[]
    for case in response['cases']:
        frame,side,round_no=case['frame'],case['side'],case['round']
        hit=[e for e in events if e.get('site')=='collision_hit' and (e['frame'],e['side'],e['round'],e['dp'],e['other'])==(frame-1,side,round_no,case['peer'],case['target'])]
        selected=[e for e in events if e.get('site')=='penalty_collision_selected' and (e['frame'],e['side'],e['round'],e['d'],e['linked_object'])==(frame-1,side,round_no,case['peer'],case['target'])]
        action=[e for e in events if e.get('site')=='penalty_contact_action' and (e['frame'],e['side'],e['round'],e['linked_object'])==(frame,side,round_no,case['peer'])]
        starts=[e for e in events if e.get('site')=='penalty_shot_final' and (e['side'],e['round'])==(side,round_no) and e['frame']<frame]
        if not(len(hit)==len(selected)==len(action)==len(starts)==1):raise ValueError('Incomplete contact chain')
        h,g,a,shot=hit[0],selected[0],action[0],starts[0]
        if not collision(rom,h):raise ValueError('Geometry did not hit')
        tables=[table for table in asset['tables'] if table['selector']==h['selector']]
        if len(tables)!=1 or tables[0]['pointer']!=h['table_pointer']:raise ValueError('Selector mismatch')
        flags=g['shot_flags'];index=shot['direction']
        if flags&0x60 or ((flags&0x100) and index not in (1,2,3)) or a['shot_flags']&0x20:raise ValueError('Native gates not satisfied')
        expected_flags=((a['shot_flags']|0x800)&~0x100)&0xffff
        observed_response=[e for e in response_events if e.get('frame')==frame and e.get('site') in ('before','after')]
        if len(observed_response)!=2 or any(e['flags']!=expected_flags for e in observed_response):raise ValueError('Observed action flags do not match')
        geometry={'x':h['x'],'y':h['y'],'z':h['z'],'otherX':h['other_x'],'otherY':h['other_y'],'otherZ':h['other_z'],'objectFlags':h['object_flags'],'offset':h['offset']}
        cases.append({'selected_frame':h['frame'],'action_frame':frame,'selector':h['selector'],'shot_index':index,
                      'selection_flags':flags,'action_flags':a['shot_flags'],'result_flags':expected_flags,
                      'geometry':geometry,'response_input':case['input'],'response_output':case['output']})
    if len(cases)!=2:raise ValueError('Unexpected contact count')
    return {'schema':'issd-penalty-contact-chain/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'response_sha256':hashlib.sha256(response_raw).hexdigest(),'tables_sha256':hashlib.sha256(asset_raw).hexdigest(),
            'cases':cases,'limits':['Two contacts from one synthetic shootout and separately instrumented replay.',
                                   'Selected contact and response are distinct script events; neither alone completes the kick.',
                                   'Selectors and coordinates are native values, not mapped to browser screen positions.',
                                   'ROM, extracted tables and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','response','response_trace','tables','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.trace,args.response,args.response_trace,args.tables)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK: 2 captured hit-to-contact-response chains')
