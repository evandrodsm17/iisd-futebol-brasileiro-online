"""Audit a single type-3 bounce after an isolated no-D-pad X release."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import load,signature,has_extended
from extract_issd_catalog import EXPECTED_MD5


def fixed(row,key):return (row[key]<<16)|row[key+'_frac']


def audit(root,baseline,rom_path,ball_type=3):
    raw=rom_path.read_bytes();header=len(raw)%0x8000
    if header not in (0,512) or hashlib.md5(raw[header:]).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    for off,code in [(0x1895d,'5636763460'),(0x18883,'38a90000f5349534a90000f5369536'),(0x189af,'ad56044a8d56044a186d56048d56'),(0x18fdd,'4e28046e2604ad28048500ad260485024e28046e2604186d2604'),(0x19019,'4e24046e2204ad24048500ad220485024e24046e2204186d2204')]:
        if raw[header+off:header+off+len(bytes.fromhex(code))]!=bytes.fromhex(code):raise ValueError(f'Unexpected code {off:x}')
    def trace(folder):
        paths=[p for p in folder.glob('issd-auto-probe-*.jsonl') if not p.name.endswith('-graphics.jsonl')]
        if len(paths)!=1:raise ValueError('Expected one trace')
        return load(paths[0])
    a,b=trace(root),trace(baseline);common=sorted(set(a['samples'])&set(b['samples']))
    if len(common)<200 or any(not has_extended(t['samples'][i]) for i in common for t in (a,b)):raise ValueError('Insufficient replay samples')
    if any(signature(a['samples'][i],True)!=signature(b['samples'][i],True) for i in common):raise ValueError('Replay mismatch')
    action=[r for r in a['samples'].values() if r.get('input_p2')=='X' and r.get('held_p2')==0x40 and any(x.get('address')==0x1900 and x.get('script')==0xd007 for x in r.get('actors',[]))]
    if not action:raise ValueError('No X command during expected actor animation')
    action_step=min(r['step'] for r in action)
    releases=[r for r in a['samples'].values() if action_step<=r['step']<=action_step+20 and r.get('link_a6')==0 and r.get('ball',{}).get('type')==ball_type]
    if not releases:raise ValueError('No matching free-ball release')
    release=min(r['frame'] for r in releases)
    events=[json.loads(line) for line in (root/'keeper-transfers.jsonl').read_text(encoding='utf8').splitlines() if line.strip()]
    if not any(e.get('type')=='session_end' for e in events):raise ValueError('Incomplete hook trace')
    impacts=[e for e in events if e.get('type')=='bounce_hook' and e['frame']>=release-2 and e['ball_type']==ball_type and e['address']=='838883']
    if len(impacts)!=1:raise ValueError('Expected one matching impact')
    frame=impacts[0]['frame'];samples=[r for r in a['samples'].values() if release<=r['frame']<frame]
    if not samples or any(r['ball']['type']!=ball_type or r['link_a6']!=0 for r in samples):raise ValueError('Shot not continuously observed as free')
    names=['83882A','838941','83895D' if ball_type==3 else '838962','838866','838883','83898D','8389AF' if ball_type==3 else '8389CE','8388BB']
    found=[e for e in events if e.get('type')=='bounce_hook' and e['frame']==frame and e['address'] in names]
    if [e['address'] for e in found]!=names or any(e['ball_type']!=ball_type for e in found):raise ValueError('Unexpected bounce path')
    impact,half_entry,_,half_done,invert,negated,branch,done=found
    expected_parameter=11 if ball_type==3 else 5
    if (impact['weather'],impact['flags'],impact['parameter'])!=(1,0,expected_parameter):raise ValueError('Unexpected bounce context')
    velocity=fixed(half_entry,'vz');reduced=velocity>>1 if ball_type==3 else (velocity>>1)+(velocity>>2)+(velocity>>3)
    if velocity!=(7*65536 if ball_type==3 else 2*65536+4096) or fixed(half_done,'vz')!=reduced or fixed(invert,'vz')!=reduced or fixed(negated,'vz')!=(-reduced)&0xffffffff:raise ValueError('Vertical response mismatch')
    for axis in ('vx','vy'):
        value=fixed(branch,axis)
        negative=bool(value&0x80000000);magnitude=(-value)&0xffffffff if negative else value
        magnitude=(magnitude>>1)+(magnitude>>2)+(magnitude>>3 if ball_type==5 else 0)
        expected=(-magnitude)&0xffffffff if negative else magnitude
        if fixed(done,axis)!=expected:raise ValueError('Horizontal response mismatch')
    if (done['z'],done['z_frac'],done['parameter'],done['flags'])!=(0,0,7 if ball_type==3 else 3,1):raise ValueError('Unexpected final bounce state')
    return {'schema':'issd-shot-bounce-audit/v1','rom_sha256':hashlib.sha256(raw[header:]).hexdigest(),'trial_sha256':a['sha256'],'baseline_sha256':b['sha256'],'trace_sha256':hashlib.sha256((root/'keeper-transfers.jsonl').read_bytes()).hexdigest(),'matched_replay_samples':len(common),'ball_type':ball_type,'release_frame':release,'bounce_frame':frame,'unowned_samples_before_bounce':len(samples),'events':found,
            'limitations':['One shot, direction, actor and weather per case; other bounce branches are not covered.','Intervening state is sampled, not continuously logged.','Comparison covers logged fields, not hidden emulator state.','Native velocities and impact thresholds are not calibrated to the browser.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--type',type=int,choices=(3,5),default=3);a=p.parse_args()
    report=audit(a.root,a.baseline,a.rom,a.type);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(f'Verified type-{a.type} bounce at frame:',report['bounce_frame'])
