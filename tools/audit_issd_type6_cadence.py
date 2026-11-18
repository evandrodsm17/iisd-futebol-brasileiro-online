"""Correlate type-6 update gaps with the emulator's per-frame lag flag."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_issd_shot_type6_flight import audit as audit_flight


def audit(rom_path,trace_path):
    flight=audit_flight(rom_path,trace_path)
    raw=trace_path.read_bytes()
    events=[json.loads(line) for line in raw.splitlines()]
    cases=[]
    for trial,flight_case in enumerate(flight['cases'],1):
        rows=[e for e in events if e.get('trial')==trial]
        frames=[e for e in rows if e['type']=='frame']
        frame_by_step={e['step']:e for e in frames}
        if len(frame_by_step)!=160 or any(not isinstance(e['lagged'],bool) for e in frames):
            raise ValueError('Missing frame or emulator lag flag')
        hooks=[e for e in rows if e['type']=='vertical' and e['site']=='83942E']
        impacts=[e for e in rows if e['type']=='vertical' and e['site']=='838883']
        if not impacts:raise ValueError('Missing first bounce')
        impact_step=min(e['step'] for e in impacts)
        first_step=min(e['step'] for e in hooks)
        updates={e['step']:e for e in hooks if first_step<=e['step']<impact_step}
        if len(updates)!=len(flight_case['steps']):raise ValueError('Mismatch with airborne audit')
        gaps=[]
        for step in range(first_step,impact_step):
            current=frame_by_step[step]
            if step in updates:
                if current['lagged'] or current['frame']!=updates[step]['frame']+1:
                    raise ValueError('Unexpected lag or frame alignment during update')
            else:
                previous=frame_by_step.get(step-1)
                if not current['lagged'] or previous is None or any(current[k]!=previous[k] for k in ('z','zFrac','vz','vzFrac','ballType','carrier')):
                    raise ValueError('Unexplained non-update frame')
                gaps.append({'step':step,'frame_after_advance':current['frame'],'lagged':current['lagged']})
        cases.append({'direction':flight_case['direction'],'first_step':first_step,'impact_step':impact_step,
                      'updates':len(updates),'lagged_without_update':gaps})
    if [len(c['lagged_without_update']) for c in cases]!=[9,10,9]:raise ValueError('Unexpected gap count')
    return {'schema':'issd-shot-type6-cadence/v1','trace_sha256':hashlib.sha256(raw).hexdigest(),'cases':cases,
            'limits':['The emulator lag flag alone does not prove the cause of a missed update.',
                      'One saved state and parameter; results are not a universal game-speed rule.',
                      'No browser cadence or physics change is implied.', 'ROM, saved state and raw trace remain local.']}


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();report=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('OK:',sum(len(c['lagged_without_update']) for c in report['cases']),'lagged frames without ball updates')
