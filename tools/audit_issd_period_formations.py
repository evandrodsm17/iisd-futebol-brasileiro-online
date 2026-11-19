"""Compare the recorded native starting formations across period transitions."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path,trace_path):
    rom=rom_path.read_bytes()
    if len(rom)%0x8000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected unheadered ROM')
    raw=trace_path.read_bytes();events=[json.loads(line) for line in raw.splitlines()]
    if events[0].get('type')!='session_start' or not events[0].get('synthetic_clock') or events[-1]!={'type':'session_end','steps':8000}:
        raise ValueError('Incomplete or unexpected capture')
    if any(e['type'] in ('score_intervention','overtime_intervention') for e in events):raise ValueError('Unexpected score or setting intervention')
    clock=[e for e in events if e['type']=='clock_intervention']
    if [e['phase'] for e in clock]!=[0,1,2,3]:raise ValueError('Unexpected accelerated periods')
    formations=[e for e in events if e['type']=='formation']
    if [f['phase'] for f in formations]!=[0,1,2,3]:raise ValueError('Missing formation')
    pairs=[]
    for left,right in zip(formations[1:],formations[2:]):
        if (left['fieldWidth'],left['fieldHeight'])!=(0x740,0x280) or (right['fieldWidth'],right['fieldHeight'])!=(0x740,0x280):raise ValueError('Unexpected field')
        a={p['address']:p for p in left['actors']};b={p['address']:p for p in right['actors']}
        if len(a)!=22 or a.keys()!=b.keys() or any(a[k]['team']!=b[k]['team'] for k in a):raise ValueError('Unexpected actor mapping')
        x_reflected=[k for k in a if a[k]['x']+b[k]['x']==left['fieldWidth']]
        y_reflected=[k for k in a if a[k]['y']+b[k]['y']==left['fieldHeight']]
        if len(x_reflected)!=22 or len(y_reflected)!=18:raise ValueError('Unexpected formation reflection')
        exceptions=[{'address':k,'team':a[k]['team'],'before_y':a[k]['y'],'after_y':b[k]['y']} for k in a if k not in y_reflected]
        keepers=[]
        for team in (0xd00,0xe00):
            ka=[p for p in a.values() if p['team']==team and p['kind']==1]
            kb=[p for p in b.values() if p['team']==team and p['kind']==1]
            if len(ka)!=1 or len(kb)!=1 or {ka[0]['x'],kb[0]['x']}!={16,1840}:raise ValueError('Unexpected keeper positions')
            keepers.append({'team':team,'address':ka[0]['address'],'before_x':ka[0]['x'],'after_x':kb[0]['x']})
        pairs.append({'from_phase':left['phase'],'to_phase':right['phase'],'actors':len(a),'reflected_x':len(x_reflected),
                      'reflected_y':len(y_reflected),'positions':[{'address':k,'team':a[k]['team'],'before_x':a[k]['x'],'after_x':b[k]['x']} for k in a], 'y_exceptions':exceptions,'keepers':keepers})
    return {'schema':'issd-period-formations/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),
            'field':{'width':0x740,'height':0x280},'comparisons':pairs,
            'limits':['Clock accelerated and menus advanced with automatic A pulses.',
                      'One saved match, stadium and formation; phase 0 snapshot is mid-play and is excluded from reflection comparisons.',
                      '22 observed actor coordinates match X reflection; the four Y exceptions prohibit assuming a universal 180-degree rotation.',
                      'Ball coordinates at these snapshots are not established as kickoff positions.',
                      'ROM, saved state and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK: 22 players reflected in X across two captured period changes')
