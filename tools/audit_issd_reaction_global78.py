"""Audit global $0078 write observations in two isolated paired replays."""
import argparse, hashlib, json
from pathlib import Path
from compare_issd_action_trials import signature, has_extended
from audit_issd_slide_reaction_choice import one_trace, sha

def audit_case(action_dir,neutral_dir,first_action,expected_frame,expected_value):
    action,neutral=one_trace(action_dir),one_trace(neutral_dir)
    a,n=action['samples'],neutral['samples']
    before=sorted(t for t in set(a)&set(n) if 0<=t<first_action)
    if not any(set(range(i,first_action-10,2))<=set(before) for i in (0,1)): raise ValueError('Incomplete baseline')
    if any(not has_extended(a[t]) or not has_extended(n[t]) or signature(a[t],True)!=signature(n[t],True) for t in before): raise ValueError('Baseline mismatch')
    path=action_dir/'reaction-global78.jsonl'
    rows=[json.loads(line) for line in path.read_text(encoding='utf8').splitlines() if line.strip()]
    reaction=[(i,r) for i,r in enumerate(rows) if r['site']=='reaction']
    if len(reaction)!=1 or reaction[0][1]['frame']!=expected_frame or reaction[0][1]['value']!=expected_value: raise ValueError('Unexpected reaction')
    writes=[r for r in rows if r['site']=='write']
    if len(writes)<10 or any(r['pc']!=0x8080de or r['d']!=0 for r in writes): raise ValueError('Unexpected global writer')
    prior=next(r for r in reversed(rows[:reaction[0][0]]) if r['site']=='write')
    if prior['a']!=expected_value: raise ValueError('Last write differs from reaction')
    pairs=[(x,y) for x,y in zip(writes,writes[1:]) if x['frame']==y['frame']]
    if len(pairs)<10 or any(y['a']!=((x['a']+y['addend']+(x['p']&1))&0xffff) for x,y in pairs): raise ValueError('Idle-loop arithmetic mismatch')
    wrap=next(((x,y) for x,y in pairs if x['a']+y['addend']+(x['p']&1)>0xffff),None)
    if not wrap: raise ValueError('Expected a carry sample')
    return {'action_trace_sha256':action['sha256'],'neutral_trace_sha256':neutral['sha256'],'hooks_sha256':sha(path),'baseline_samples':len(before),'write_count':len(writes),'same_frame_pairs':len(pairs),'mismatched_pairs':0,'reaction':reaction[0][1],'last_prior_write':prior,'example_pair':list(pairs[0]),'carry_pair':list(wrap)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--jump',type=Path,required=True);p.add_argument('--jump-neutral',type=Path,required=True);p.add_argument('--fall',type=Path,required=True);p.add_argument('--fall-neutral',type=Path,required=True);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    result={'schema':'issd-reaction-global78-observation/v1','state_sha256':sha(args.state),'jump':audit_case(args.jump,args.jump_neutral,420,4221,0x410b),'fall':audit_case(args.fall,args.fall_neutral,480,4280,0x1088),'limitations':['Hooks record only the specified two-frame windows and logged baseline fields.','Memory-write callback timing is specific to this BizHawk core; A and P are the post-ADC CPU state.','The loop explains writes in these windows, not all possible writes to global 78.','Changing the field causally and mapping its timing to the browser are not tested.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print('OK: idle loop matches',result['jump']['same_frame_pairs']+result['fall']['same_frame_pairs'],'observed pairs')
