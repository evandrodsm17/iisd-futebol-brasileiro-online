"""Audit paired defensive replays with explicitly synthetic foul settings."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_issd_defense_approach import pair, only_trace
from audit_issd_defense_opponent import segments
from compare_issd_action_trials import signature


def read(path):
    raw=path.read_bytes()
    return [json.loads(line) for line in raw.splitlines() if line.strip()],hashlib.sha256(raw).hexdigest()


def audit(root,state):
    cases={};raw_traces={}
    for value in (0,1):
        base=root/str(value);comparison=pair(base/'A',base/'NEUTRAL','Right')
        if len(comparison['gate_events'])!=1 or comparison['gate_events'][0]['carry']!=0:
            raise ValueError('Expected accepted natural contact')
        logs={};hashes={};override_records={}
        for button in ('A','NEUTRAL'):
            directory=base/button;paths=list(directory.glob('issd-auto-probe-*.jsonl'))
            if len(paths)!=1:raise ValueError('Expected one driver trace')
            rows,_=read(paths[0]);overrides=[r for r in rows if r.get('type')=='synthetic_foul_setting']
            if len(overrides)!=1 or overrides[0]['address']!=0x1e50 or overrides[0]['value']!=value:
                raise ValueError('Missing declared synthetic override')
            override_records[button]=overrides[0]
            records,hashes[button]=read(directory/'defense-opponent.jsonl')
            logs[button]=records;raw_traces[(value,button)]=only_trace(directory)
        a={r['frame']:r for r in logs['A'] if r['type']=='frame_end'}
        n={r['frame']:r for r in logs['NEUTRAL'] if r['type']=='frame_end'}
        expected=set(range(4274,4551))
        if set(a)!=expected or set(n)!=expected:raise ValueError('Incomplete frame window')
        if any(x['foul_setting']!=value for x in list(a.values())+list(n.values())):
            raise ValueError('Foul setting changed in observation')
        first=comparison['first_input_frame']
        for f in range(4274,first):
            for key in ('player','opponent','ball','link_a6','phase','foul_setting','global_11fa','event_12f6'):
                if a[f][key]!=n[f][key]:raise ValueError('Pre-action frame mismatch')
        hooks=[r for r in logs['A'] if r['type']=='execution' and r['frame']==4280 and
               (r['site'].startswith('foul_') or r['site']=='after_foul_gate')]
        names=[r['site'] for r in hooks]
        wanted=(['foul_gate_entry','foul_branch_47','foul_branch_4f','foul_branch_6a','foul_return_clear','after_foul_gate']
                if value==0 else ['foul_gate_entry','foul_return_clear','after_foul_gate'])
        if names!=wanted or hooks[-1]['p']&1:raise ValueError(f'Unexpected gate route: {names}')
        if value==0 and not (hooks[0]['event_12f6']&0x100==0 and hooks[-1]['event_12f6']&0x100):
            raise ValueError('Expected observed bit transition')
        if value==1 and hooks[-1]['event_12f6']&0x100:raise ValueError('Unexpected bit transition')
        if any(r['phase']!=0 for r in list(a.values())+list(n.values())):raise ValueError('Unexpected phase')
        cases[str(value)]={'synthetic_value':value,'override_records':override_records,'baseline_samples':comparison['baseline_samples'],
                           'action_probe_sha256':hashes['A'],'neutral_probe_sha256':hashes['NEUTRAL'],
                           'gate_events':hooks,'action_segments':segments([a[f] for f in sorted(a)]),
                           'neutral_segments':segments([n[f] for f in sorted(n)]),
                           'last_opponent_state':a[4550]['opponent']['state'],
                           'last_opponent_timer':a[4550]['opponent']['f70']}
    x,y=raw_traces[(0,'A')]['samples'],raw_traces[(1,'A')]['samples']
    before=sorted(t for t in set(x)&set(y) if 0<=t<480)
    if any(signature(x[t],True)!=signature(y[t],True) for t in before):
        raise ValueError('Cross-setting logged baseline differs')
    return {'schema':'issd-foul-setting-paired/v1',
            'declared_state_sha256':hashlib.sha256(state.read_bytes()).hexdigest(),
            'cross_setting_baseline_samples':len(before),'cases':cases,
            'limitations':['Setting $1E50 was deliberately overridden in isolated RAM; these are synthetic setting experiments.',
                           'Logged baseline equality does not prove identical hidden state or random evolution after the action.',
                           'Neither observed route establishes that a foul is awarded or identifies restart behavior.',
                           'The numeric values are not named ON/OFF without independent menu-to-RAM evidence.',
                           'This is one DF7F contact, not a completed DB25 tackle or a general foul rule.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();r=audit(a.root,a.state);a.output.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
    print('paired settings:',len(r['cases']),'baseline samples:',r['cross_setting_baseline_samples'])
