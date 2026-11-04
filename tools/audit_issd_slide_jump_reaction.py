"""Audit the ball holder's forward-jump reaction in paired natural replays."""
import argparse, hashlib, json
from pathlib import Path
from compare_issd_action_trials import load, signature, has_extended
from extract_issd_catalog import EXPECTED_MD5
from render_issd_descriptor_sprite import descriptor_tiles


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return [json.loads(line) for line in p.read_text(encoding='utf8').splitlines() if line.strip()]
def trace(root):
    paths=list(root.glob('issd-auto-probe-*.jsonl'))
    if len(paths)!=1:raise ValueError('Expected one replay trace')
    if not any(x.get('type')=='session_end' and x.get('experiment_triggered') for x in read(paths[0])):raise ValueError('Incomplete replay')
    return load(paths[0])

def audit(root,state,rom_path):
    rom=rom_path.read_bytes()
    if len(rom)!=0x200000 or hashlib.md5(rom).hexdigest()!=EXPECTED_MD5:raise ValueError('Unexpected ROM')
    ad,nd=root/'A',root/'NEUTRAL';at,nt=trace(ad),trace(nd);a,n=at['samples'],nt['samples']
    before=sorted(t for t in set(a)&set(n) if 0<=t<420)
    if not any(set(range(i,410,2))<=set(before) for i in (0,1)):raise ValueError('Incomplete baseline')
    if any(not has_extended(a[t]) or not has_extended(n[t]) or signature(a[t],True)!=signature(n[t],True) for t in before):raise ValueError('Baseline mismatch')
    if any(a[t]['held_p1']!=0x80 or n[t]['held_p1']!=0 for t in range(420,426)):raise ValueError('Action input mismatch')
    if any(a[t]['held_p2']!=0 or n[t]['held_p2']!=0 for t in range(420,450)):raise ValueError('P2 unexpectedly pressed a button')
    attacker=a[419]['selected_p1'];carrier=a[419]['link_a6'];first=a[420]['frame']-1
    if attacker!=0xd00 or carrier!=0x1900 or a[420]['actor']['state']!=0x2d0 or a[420]['actor']['script']!=0xdb25:raise ValueError('Unexpected action or actors')
    def player(s,t,addr):return next(x for x in s[t]['actors'] if x['address']==addr)
    if any(a[t]['link_a6']!=carrier or n[t]['link_a6']!=carrier for t in range(420,461)):raise ValueError('Ball link changed during observation')
    hooks=read(ad/'slide-contact-route.jsonl');control=read(nd/'slide-contact-route.jsonl')
    if any(r['site'] in ('jump_entry','jump_setup','jump_update','jump_landing') and first<=r['frame']<=first+30 for r in control):raise ValueError('Jump present in control')
    jump=[r for r in hooks if r['site'] in ('reaction_dispatch','jump_entry','jump_setup','jump_update','jump_landing') and first<=r['frame']<=first+30]
    starts=[r for r in jump if r['site'] in ('reaction_dispatch','jump_entry','jump_setup')]
    if [r['site'] for r in starts]!=['reaction_dispatch','jump_entry','jump_setup'] or any(r['actor_source']!=attacker or r['actor_reaction']&15!=4 or r['link_a6']!=carrier for r in starts):raise ValueError('Unexpected jump entry')
    updates=[r for r in jump if r['site']=='jump_update'];land=[r for r in jump if r['site']=='jump_landing']
    if len(updates)!=23 or len(land)!=1 or any(r['state']!=0x370 or r['script']!=0xdf4d or r['link_a6']!=carrier for r in updates):raise ValueError('Unexpected jump timeline')
    signed=lambda x:x if x<0x8000 else x-0x10000
    height=[signed(r['actor_z']) for r in updates]
    if min(height)>=0 or height[0]!=0 or height[-1]!=2:raise ValueError('Unexpected vertical trajectory')
    expected=[(0xbcd6,0x9ce760),(0xbcdf,0x9ce8e4),(0xbce8,0x9cea28)]
    for descriptor,address in expected:
        _,meta=descriptor_tiles(rom,descriptor)
        if int(meta['graphics_source'][1:],16)!=address:raise ValueError('Jump descriptor source mismatch')
    observed=[]
    for t in range(426,449):
        v=player(a,t,carrier)
        if v['state']!=0x370 or v['script']!=0xdf4d or v['direction']!=4:raise ValueError('Unexpected carrier action')
        if not observed or observed[-1]!=v['descriptor']:observed.append(v['descriptor'])
    if observed!=[x[0] for x in expected]:raise ValueError('Unexpected jump sequence')
    if player(a,449,carrier)['state']!=0xe8 or player(a,465,carrier)['state']!=0xb8:raise ValueError('Unexpected recovery')
    if any(player(n,t,carrier)['state']!=0xb8 for t in range(420,450)):raise ValueError('Control changed carrier state')
    timeline=[]
    for t in (419,420,425,426,430,440,445,448,449,455,460,465):
        def snapshot(s):
            r=s[t];v=player(s,t,carrier);p=player(s,t,attacker)
            return {'attacker_state':p['state'],'attacker_script':p['script'],'carrier_state':v['state'],'carrier_script':v['script'],'carrier_descriptor':v['descriptor'],'ball_link':r['link_a6'],'ball_z':r['ball']['z'],'p2_held':r['held_p2']}
        timeline.append({'elapsed':t,'action':snapshot(a),'control':snapshot(n)})
    return {'schema':'issd-slide-jump-reaction/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),'declared_state_sha256':sha(state),'action_trace_sha256':at['sha256'],'control_trace_sha256':nt['sha256'],'action_hooks_sha256':sha(ad/'slide-contact-route.jsonl'),'control_hooks_sha256':sha(nd/'slide-contact-route.jsonl'),
            'baseline_samples':len(before),'attacker':attacker,'carrier':carrier,'first_action_frame':first,'input_frames':6,'jump_start':starts,'jump_updates':updates,'jump_landing':land[0],
            'descriptors':[{'descriptor':d,'graphics_source':f'${addr:06X}'} for d,addr in expected],'timeline':timeline,
            'limitations':['One paired replay; other angles, skills, rules and teams are not generalized.',
              'P2 held no button during the observed jump, but unobserved internal inputs and AI decisions are not ruled out.',
              'The data supports a jump-like reaction with the ball link retained, not all conditions that trigger evasion.',
              'Visual OAM composition, full collision outcome and browser coordinate scaling remain unverified.',
              'Matching logged baseline fields is not equality of complete emulator state.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();r=audit(args.root,args.state,args.rom)
    args.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf8');print('OK: paired slide and ball-holder jump,',r['baseline_samples'],'baseline samples')
