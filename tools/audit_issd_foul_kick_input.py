"""Compare two isolated P2 restart-button trials with the same no-button replay."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
def actor(row): return next(a for a in row['actors'] if a['address'] == 0x1200)


def audit(root, state):
    trials = {}
    for button in ('NEUTRAL', 'A', 'B'):
        directory = root / button
        paths = list(directory.glob('issd-auto-probe-*.jsonl'))
        if len(paths) != 1: raise ValueError('Expected exactly one input trace')
        rows = read(paths[0])
        for kind, address in (('synthetic_foul_setting',0x1e50),('synthetic_referee',0x1e58)):
            marks = [r for r in rows if r.get('type') == kind]
            if len(marks) != 1 or marks[0]['address'] != address or marks[0]['value'] != 0:
                raise ValueError('Missing synthetic RAM marker')
        marker = [r for r in rows if r.get('type') == 'restart_probe']
        if button == 'NEUTRAL':
            if marker: raise ValueError('Control contains restart command')
        elif marker != [{'type':'restart_probe','controller':2,'button':button,'relative_start':800,'duration':6}]:
            raise ValueError('Incorrect probe declaration')
        samples = {r['step']:r for r in rows if 'actors' in r}
        if not samples or not any(r.get('type')=='session_end' and r['steps']==5401 for r in rows):
            raise ValueError('Replay did not finish')
        probe = read(directory/'defense-opponent.jsonl')
        frames = {r['frame']:r for r in probe if r['type']=='frame_end'}
        if set(frames) != set(range(4274,5001)): raise ValueError('Incomplete frame trace')
        trials[button] = {'samples':samples, 'frames':frames, 'input_sha256':sha(paths[0]), 'probe_sha256':sha(directory/'defense-opponent.jsonl')}
    base=trials['NEUTRAL']['samples']
    baseline_steps=sorted(s for s in base if s<4801)
    for button in ('A','B'):
        trial=trials[button]['samples']
        if [s for s in trial if s<4801] != baseline_steps or any(trial[s]!=base[s] for s in baseline_steps):
            raise ValueError('Logged baseline mismatch')
        if [(s, trial[s]['input_p2']) for s in range(4802,4807,2)] != [(s,button) for s in range(4802,4807,2)]:
            raise ValueError('Missing sampled P2 button pulse')
        if trial[4802]['controls'][1]['actor']!=0x1200: raise ValueError('P2 does not control selected actor')
    for f in range(4590,5001):
        if trials['NEUTRAL']['frames'][f]['phase']!=4: raise ValueError('Control unexpectedly left phase 4')
    cases={}
    for button, ball_type in [('A',3),('B',2)]:
        trial=trials[button];f=trial['frames'];s=trial['samples']
        if f[4612]['phase']!=4 or f[4613]['phase']!=0 or f[4613]['ball']['type']!=ball_type:
            raise ValueError('Unexpected phase or ball transition')
        if [actor(s[k])['state'] for k in (4800,4802,4812,4818)]!=[0x460,0x468,0x470,0x470]:
            raise ValueError('Unexpected selected-actor states')
        cases[button]={'input_sha256':trial['input_sha256'],'probe_sha256':trial['probe_sha256'],
            'selected_actor':0x1200,'phase_change_frame':4613,'ball_type':ball_type,
            'samples':[{ 'step':k,'frame':s[k]['frame'],'input_p2':s[k]['input_p2'],
                'state':actor(s[k])['state'],'script':actor(s[k])['script'],'ball':s[k]['ball'],'phase':s[k]['phase']}
                for k in (4800,4802,4812,4818,4820)]}
    return {'schema':'issd-foul-kick-input/v1','declared_state_sha256':sha(state),'synthetic_referee':0,'synthetic_foul_setting':0,
        'comparison':'same foul replay, with a P2 A/B pulse or no later input','baseline_sample_count':len(baseline_steps),
        'control_input_sha256':trials['NEUTRAL']['input_sha256'],'control_probe_sha256':trials['NEUTRAL']['probe_sha256'],
        'cases':cases,'limitations':['This is one DF7F foul with synthetic referee and foul-setting values, not every restart.',
          'Inputs sampled every two steps; transition frame is established by the separate frame-end probe.',
          'Ball velocities and height are raw unsigned 16-bit values, not calibrated world units.',
          'Labels pass, shot and full animation composition are not established by button identity alone.',
          'Game clock and all hidden state were not measured; equivalent logged baselines do not prove identical hidden state.',
          'Declared save-state identity is not authenticated by the traces.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('--state',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=audit(a.root,a.state);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('foul kick input comparison: OK (neutral, A and B)')
