"""Audit consecutive deferred penalty checks after two captured contacts."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def check(snapshot):
    timer=snapshot['timer']
    if (snapshot['x']|snapshot['y'])&0xff00:
        timer=(timer-1)&0xffff
        if timer&0x8000:return timer,True,'timer'
    stopped=not(snapshot['field28']|snapshot['field29']|snapshot['field32']|snapshot['field33']|snapshot['height'])
    return timer,stopped,'fields_zero' if stopped else None


def audit(rom_path,directory,chain_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    expected=bytes.fromhex('a5 08 05 0c 89 00 ff f0 10 c6 24 10 0c ad aa 14 29 ff f7 8d aa 14 4c c1 8d a5 28 05 29 05 32 05 33 05 10 f0 e8 6b')
    if rom[0x60e62:0x60e62+len(expected)]!=expected:raise ValueError('Unexpected deferred instructions')
    raw=(directory/'deferred-checks.jsonl').read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    if events[0].get('site')!='session_start' or events[-1].get('site')!='session_end' or any(e.get('site')=='error' for e in events):raise ValueError('Incomplete capture')
    driver_path,=directory.glob('issd-auto-probe-*.jsonl');driver_raw=driver_path.read_bytes();driver=[json.loads(line) for line in driver_raw.splitlines()]
    configs=[e for e in driver if e.get('type')=='penalty_direction_config']
    if len(configs)!=1 or configs[0].get('direction')!='Right' or configs[0].get('controllers')!='p1' or not any(e.get('type')=='synthetic_clock' for e in driver) or not any(e.get('type')=='synthetic_score' for e in driver) or not any(e.get('type')=='session_end' for e in driver):raise ValueError('Unexpected driver')
    chain_raw=chain_path.read_bytes();chain=json.loads(chain_raw)
    if chain['schema']!='issd-penalty-contact-chain/v1' or len(chain['cases'])!=2:raise ValueError('Unexpected contact report')
    cases=[]
    for n,item in enumerate(chain['cases']):
        checks=[e for e in events if e.get('site')=='check' and e['frame']>item['action_frame'] and (n==1 or e['frame']<chain['cases'][n+1]['action_frame'])]
        if len(checks)!=39 or any(b['frame']!=a['frame']+1 for a,b in zip(checks,checks[1:])):raise ValueError('Unexpected check sequence')
        outputs=[];previous=None
        for i,e in enumerate(checks):
            if previous is not None and e['timer']!=previous:raise ValueError('Unexpected timer change between checks')
            timer,final,reason=check(e)
            if final!=(i==len(checks)-1):raise ValueError('Unexpected finalization')
            outputs.append({'frame':e['frame'],'snapshot':{k:e[k] for k in ('x','y','height','timer','field28','field29','field32','field33')},
                            'flags':e['flags'],'result_timer':timer,'finalize':final,'reason':reason})
            previous=timer
        last=checks[-1]
        final=[e for e in events if e.get('site')=='finalize' and e['frame']==last['frame'] and e['d']==last['d']]
        resolved=[e for e in events if e.get('site')=='resolved' and e['frame']==last['frame'] and e['d']==last['d']]
        if len(final)!=1 or len(resolved)!=1 or final[0]['timer']!=previous or resolved[0]['timer']!=previous or final[0]['flags']!=last['flags'] or resolved[0]['flags']!=(last['flags']&0xf7ff):raise ValueError('Finalization mismatch')
        if any(final[0][k]!=resolved[0][k] or last[k]!=resolved[0][k] for k in ('home','away')):raise ValueError('Counters changed during deferred transition')
        cases.append({'action_frame':item['action_frame'],'initial_score':[checks[0]['home'],checks[0]['away']],
                      'resolved_frame':last['frame'],'resolved_flags':resolved[0]['flags'],'checks':outputs})
    return {'schema':'issd-penalty-deferred-checks/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'driver_sha256':hashlib.sha256(driver_raw).hexdigest(),'contact_report_sha256':hashlib.sha256(chain_raw).hexdigest(),
            'cases':cases,'limits':['Two contacts in one synthetic replay; both observed endings use timer underflow.',
            'Snapshots are recorded after earlier native motion and stop routines, not before them.',
            'A resolved contact is not itself a scored or completed kick; later native processing remains separate.',
            'Other contact types, stopped-field termination and full game conditions are not established by this replay.',
            'ROM and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','directory','chain','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();result=audit(args.rom,args.directory,args.chain)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK: 78 consecutive checks, two timer resolutions, no counter change')
