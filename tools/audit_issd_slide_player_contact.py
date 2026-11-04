"""Audit a paired natural slide/player collision without changing emulator RAM."""
import argparse, hashlib, json
from pathlib import Path
from compare_issd_action_trials import load, signature, has_extended
from issd_contact_volume import contact_volume
from extract_issd_catalog import EXPECTED_MD5


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf8').splitlines() if x.strip()]
def trace(root):
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1:raise ValueError('Expected exactly one action trace')
    all_rows=rows(paths[0]);ends=[r for r in all_rows if r.get('type')=='session_end']
    if len(ends)!=1 or not ends[0].get('experiment_triggered'):raise ValueError('Incomplete replay')
    return load(paths[0])

def audit(root,state,rom):
    raw=rom.read_bytes()
    if len(raw)!=0x200000 or hashlib.md5(raw).hexdigest()!=EXPECTED_MD5 or raw[0xd003:0xd007]!=bytes.fromhex('0c000800'):raise ValueError('Unexpected ROM or overlap table')
    ap,np=root/'A',root/'NEUTRAL';at,nt=trace(ap),trace(np);a,n=at['samples'],nt['samples']
    before=sorted(t for t in set(a)&set(n) if 0<=t<480)
    if not any(set(range(i,480,2))<=set(before) for i in (0,1)):raise ValueError('Missing baseline coverage')
    if any(not has_extended(a[t]) or not has_extended(n[t]) or signature(a[t],True)!=signature(n[t],True) for t in before):raise ValueError('Logged baseline mismatch')
    if any(a[t]['held_p1']!=0x180 or n[t]['held_p1']!=0x100 for t in range(480,486)):raise ValueError('Input mismatch')
    actor=a[479]['selected_p1'];opponent=a[479]['link_a6'];start=a[480]['frame']-1
    if actor!=0xd00 or opponent!=0x1900 or a[480]['actor']['state']!=0x2d0 or a[480]['actor']['script']!=0xdb25:raise ValueError('Unexpected slide actor')
    events=rows(ap/'slide-contact-route.jsonl');neutral=rows(np/'slide-contact-route.jsonl')
    if [r for r in events if r['frame']<start]!=[r for r in neutral if r['frame']<start]:raise ValueError('Instruction baseline mismatch')
    window=[r for r in events if r['frame']==start+5];sites=[r['site'] for r in window]
    required=['slide_handler','proximity_entry','proximity_return','ball_gate_entry','player_overlap_entry','player_overlap_return','opponent_condition_entry','clear_link','after_clear_link']
    if sites!=required:raise ValueError(f'Unexpected instruction sequence: {sites}')
    by={r['site']:r for r in window};prox=by['proximity_return'];over=by['player_overlap_return']
    if not (prox['p']&1 and over['p']&1==0 and over['x']==opponent and not(by['player_overlap_entry']['flags']&0x20) and over['flags']&0x20):raise ValueError('Unexpected overlap gate result')
    entry=by['player_overlap_entry'];coords=[]
    for base,i in ((18,0),(12,1)):
        delta=(base+entry['actor_xy'][i]+entry['offset_xy'][i]-entry['target_xy'][i])&0xffff
        coords.append({'axis':'x' if i==0 else 'y','delta':delta,'limit':base*2,'inside':delta<base*2})
    if entry['target']!=opponent or entry['target_flags']&0x100 or any(not axis['inside'] for axis in coords):raise ValueError('Overlap geometry mismatch')
    if not (by['clear_link']['dp']==opponent and by['clear_link']['link_a6']==opponent and by['after_clear_link']['link_a6']==0):raise ValueError('Unexpected link transition')
    if any(r['actor']==actor and r['site'] in required for r in neutral if start<=r['frame']<=start+12):raise ValueError('Control took slide path')
    gates=[r for r in rows(ap/'slide-ball-gate.jsonl') if r['actor']==actor and start<=r['frame']<=start+12]
    if len(gates)!=1 or gates[0]['synthetic'] or gates[0]['script']!=0xdb25 or gates[0]['carry']!=1:raise ValueError('Unexpected ball gate')
    g=gates[0];expected=contact_volume([12,24,8,16,8,16],g['actor_xyz'],g['offset_xyz'],g['ball_xyz'],phase=g['phase'],flag_11fa=g['global'],actor_flags=g['flags'])
    if expected['carry']!=g['carry'] or expected['actor_flags']!=g['flags_after']:raise ValueError('Ball gate model mismatch')
    def snap(s,t):
        r=s[t];p=next(v for v in r['actors'] if v['address']==actor);o=next(v for v in r['actors'] if v['address']==opponent)
        return {'elapsed':t,'selected':r['selected_p1'],'actor_state':p['state'],'actor_script':p['script'],'opponent_state':o['state'],'opponent_script':o['script'],'link_a6':r['link_a6'],'ball':r['ball']}
    timeline=[{'action':snap(a,t),'control':snap(n,t)} for t in (479,480,484,485,486,490,500,510)]
    if not (a[484]['link_a6']==opponent and a[485]['link_a6']==0 and n[485]['link_a6']==opponent and a[485]['ball']['type']==1 and n[485]['ball']['type']==0):raise ValueError('Unexpected paired ball change')
    if [(snap(a,t)['opponent_state'],snap(a,t)['opponent_script']) for t in (485,500,510)]!=[(0x328,0xdb05),(0x330,0xdb15),(0x360,0xddac)]:raise ValueError('Unexpected opponent response')
    if any(snap(n,t)['opponent_state']!=0xb8 for t in (485,500,510)):raise ValueError('Unexpected control opponent response')
    return {'schema':'issd-slide-player-contact/v1','declared_state_sha256':sha(state),'action_trace_sha256':at['sha256'],'control_trace_sha256':nt['sha256'],
            'action_probe_sha256':sha(ap/'slide-contact-route.jsonl'),'control_probe_sha256':sha(np/'slide-contact-route.jsonl'),'gate_sha256':sha(ap/'slide-ball-gate.jsonl'),
            'baseline_samples':len(before),'actor':actor,'opponent':opponent,'first_action_frame':start,'input_frames':6,'event_sequence':window,
            'ball_gate':{'observation':g,'model_rejected_by':expected['rejected_by']},'player_overlap':{'table':'$81:D003','words':[12,8],'axes':coords},'timeline':timeline,
            'limitations':['Only one replay geometry, actor pair, speed and direction are observed.',
                           'Paired baseline compares logged fields, not all hidden emulator state.',
                           'Hooks establish order and state transitions but do not trace every instruction between them.',
                           'Coordinates and velocities remain native units; browser scale and foul outcomes are not proven.',
                           'Captured contact does not establish the general rule for all slide collisions.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();report=audit(args.root,args.state,args.rom)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print('OK: paired natural slide-player contact,',report['baseline_samples'],'baseline samples')
