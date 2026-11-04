"""Audit paired referee-setting replay paths, including the recorded foul screen."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageChops

from audit_issd_defense_approach import pair, only_trace
from audit_issd_defense_opponent import segments
from compare_issd_action_trials import signature


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def audit(root,state):
    cases={};traces={}
    for referee in range(3):
        base=root/str(referee);comparison=pair(base/'A',base/'NEUTRAL','Right')
        if len(comparison['gate_events'])!=1 or comparison['gate_events'][0]['carry']!=0:
            raise ValueError('Expected passive accepted contact')
        probes={};tracepaths={}
        for button in ('A','NEUTRAL'):
            directory=base/button;paths=list(directory.glob('issd-auto-probe-*.jsonl'))
            if len(paths)!=1:raise ValueError('Expected one replay trace')
            tracepaths[button]=paths[0];rows=read(paths[0]);traces[(referee,button)]=only_trace(directory)
            for key,address,value in [('synthetic_foul_setting',0x1e50,0),('synthetic_referee',0x1e58,referee)]:
                overrides=[r for r in rows if r.get('type')==key]
                if len(overrides)!=1 or overrides[0]['address']!=address or overrides[0]['value']!=value:
                    raise ValueError('Missing synthetic setting marker')
            probes[button]=read(directory/'defense-opponent.jsonl')
        action={r['frame']:r for r in probes['A'] if r['type']=='frame_end'}
        neutral={r['frame']:r for r in probes['NEUTRAL'] if r['type']=='frame_end'}
        if set(action)!=set(range(4274,4551)) or set(neutral)!=set(action):raise ValueError('Incomplete paired frame window')
        if any(r['foul_setting']!=0 or r['referee']!=referee for r in list(action.values())+list(neutral.values())):
            raise ValueError('Settings changed during observation')
        for key in ('player','opponent','ball','phase','link_a6','event_12f6','foul_setting','referee'):
            if action[4274][key]!=neutral[4274][key]:raise ValueError('Additional baseline mismatch')
        hooks=[r for r in probes['A'] if r['type']=='execution' and r['frame']==4280 and
               (r['site'].startswith('foul_') or r['site']=='after_foul_gate')]
        names=[r['site'] for r in hooks]
        expected=(['foul_gate_entry','foul_branch_47','foul_branch_125','after_foul_gate'] if referee==0 else
                  ['foul_gate_entry','foul_branch_47','foul_branch_4f','foul_branch_6a','foul_return_clear','after_foul_gate'])
        if names!=expected:raise ValueError(f'Unexpected referee route: {names}')
        if referee==0:
            if not (hooks[-1]['p']&1 and hooks[-1]['foul_00ba']==3 and action[4282]['phase']==4):
                raise ValueError('Missing positive phase transition')
        elif hooks[-1]['p']&1 or any(r['phase']!=0 for r in action.values()):
            raise ValueError('Unexpected phase in comparison')
        if any(r['phase']!=0 or r['foul_00ba']!=0 for r in neutral.values()):raise ValueError('Unexpected neutral phase')
        shots={}
        for button in ('A','NEUTRAL'):
            sample=traces[(referee,button)]['samples'].get(510)
            if not sample or sample['step']!=4511 or sample['frame']!=4306:
                raise ValueError('Screenshot step is not aligned with sampled frame')
            candidates=list((base/button).glob('*-4511.png'))
            if len(candidates)!=1:raise ValueError('Missing matched screenshot')
            shots[button]=candidates[0]
        with Image.open(shots['A']) as a,Image.open(shots['NEUTRAL']) as b:
            if a.size!=(256,224) or b.size!=(256,224):raise ValueError('Unexpected screenshot size')
            bbox=ImageChops.difference(a.convert('RGB'),b.convert('RGB')).getbbox()
        cases[str(referee)]={'synthetic_referee':referee,'synthetic_foul_setting':0,
            'baseline_samples':comparison['baseline_samples'],'action_trace_sha256':comparison['action_trace_sha256'],
            'control_trace_sha256':comparison['neutral_trace_sha256'],'action_probe_sha256':sha(base/'A'/'defense-opponent.jsonl'),
            'control_probe_sha256':sha(base/'NEUTRAL'/'defense-opponent.jsonl'),
            'gate_events':hooks,'action_segments':segments([action[f] for f in sorted(action)]),
            'control_segments':segments([neutral[f] for f in sorted(neutral)]),
            'screenshot_step':4511,'screenshot_frame':4306,
            'action_screenshot_sha256':sha(shots['A']),'control_screenshot_sha256':sha(shots['NEUTRAL']),
            'screenshot_difference_bbox':list(bbox) if bbox else None}
    sample_sets=[traces[(i,'A')]['samples'] for i in range(3)]
    common=set.intersection(*(set(s) for s in sample_sets));before=sorted(t for t in common if 0<=t<480)
    if any(signature(sample_sets[0][t],True)!=signature(s[t],True) for s in sample_sets[1:] for t in before):
        raise ValueError('Cross-referee logged baseline differs')
    return {'schema':'issd-foul-referee-replay/v1','declared_state_sha256':sha(state),
            'cross_referee_baseline_samples':len(before),'cases':cases,
            'visual_observation':'The local referee-0 action screenshot visibly shows FOUL; the paired neutral screenshot does not. This was visually inspected, not machine-read.',
            'limitations':['Referee and foul setting were overridden synthetically in isolated RAM.',
                           'Logged baseline equality does not prove all hidden state or later random evolution equal.',
                           'This is one DF7F contact and does not establish a general foul rule or DB25 tackle result.',
                           'The screenshot comparison detects image differences but does not automatically read the text.',
                           'Phase and restart semantics beyond the observed window remain to be verified.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('paired referee settings:',len(r['cases']),'baseline samples:',r['cross_referee_baseline_samples'])
