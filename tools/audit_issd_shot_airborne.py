"""Verify the observed airborne branch after one controlled X-button shot."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import load, signature, has_extended
from extract_issd_catalog import EXPECTED_MD5


def fixed(row,integer,fraction):return (row[integer]<<16)|row[fraction]


def audit(root,baseline,rom_path):
    raw=rom_path.read_bytes();header=len(raw)%0x8000
    if header not in (0,512) or hashlib.md5(raw[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    for off,code in ((0x1882a,'18b50e7534950eb5107536'),(0x18863,'951060'),(0x1942e,'b5581875349534b536690000953660')):
        if raw[header+off:header+off+len(bytes.fromhex(code))]!=bytes.fromhex(code):raise ValueError('Unexpected ROM instructions')
    def trace(folder):
        paths=[p for p in folder.glob('issd-auto-probe-*.jsonl') if not p.name.endswith('-graphics.jsonl')]
        if len(paths)!=1:raise ValueError('Expected one replay trace')
        return load(paths[0])
    trial,control=trace(root),trace(baseline)
    common=sorted(set(trial['samples'])&set(control['samples']))
    if len(common)<200 or any(not has_extended(t['samples'][i]) for i in common for t in (trial,control)):raise ValueError('Insufficient comparable samples')
    mismatch=[i for i in common if signature(trial['samples'][i],True)!=signature(control['samples'][i],True)]
    if mismatch:raise ValueError(f'Replay mismatch at {mismatch[0]}')
    actions=[r for r in trial['samples'].values() if r.get('input_p2')=='X' and r.get('held_p2')==0x40]
    if not actions:raise ValueError('No isolated X command')
    releases=[r for r in actions if r.get('link_a6')==0 and r.get('ball',{}).get('type')==3]
    if not releases:raise ValueError('No type-3 release during X')
    release_frame=min(r['frame'] for r in releases)
    events=[json.loads(line) for line in (root/'keeper-transfers.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
    if not any(e.get('type')=='session_end' for e in events):raise ValueError('Incomplete capture')
    groups={}
    for row in events:
        if row.get('type')=='ball_vertical':groups.setdefault(row['frame'],[]).append(row)
    verified=[]
    for frame,items in sorted(groups.items()):
        if not release_frame-2<=frame<release_frame+60:continue
        names=[r['address'] for r in items]
        if names!=['83941F','83942E','83882A','838863','838865']:continue
        entry,accel,before,store,after=items
        if any(r['ball_type']!=3 or r['xreg']!=0x400 or r['link_a6']!=0 for r in items):continue
        velocity=(fixed(accel,'vz','vz_frac')+accel['gravity'])&0xffffffff
        if fixed(before,'vz','vz_frac')!=velocity:raise ValueError('Acceleration mismatch')
        position=(fixed(before,'z','z_frac')+velocity)&0xffffffff
        if not position&0x80000000:continue
        if store['a']!=position>>16 or fixed(after,'z','z_frac')!=position:raise ValueError('Height integration mismatch')
        verified.append({'frame':frame,'position_before':fixed(accel,'z','z_frac'),'velocity_before':fixed(accel,'vz','vz_frac'),'gravity_word':accel['gravity'],'velocity_after':velocity,'position_after':position})
    if not verified:raise ValueError('No verified airborne shot samples')
    return {'schema':'issd-shot-airborne-audit/v1','rom_sha256':hashlib.sha256(raw[header:]).hexdigest(),'trial_sha256':trial['sha256'],'baseline_sha256':control['sha256'],'trace_sha256':hashlib.sha256((root/'keeper-transfers.jsonl').read_bytes()).hexdigest(),'matched_replay_samples':len(common),'release_frame':release_frame,'verified_steps':len(verified),'gravity_words':sorted({x['gravity_word'] for x in verified}),'first':verified[0],'last':verified[-1],
            'limitations':['One X-button release, actor, state, weather and direction.','Only the airborne negative-height path for type 3; landing and other types are excluded.','Replay equality covers logged fields only, not hidden state.','Native units are not calibrated to Canvas.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    report=audit(a.root,a.baseline,a.rom);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print('Verified airborne steps:',report['verified_steps'])
