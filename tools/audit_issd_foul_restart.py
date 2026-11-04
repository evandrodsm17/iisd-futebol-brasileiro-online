"""Audit the extended, synthetic-referee foul restart replay and its neutral control."""
import argparse
import hashlib
import json
from pathlib import Path
from audit_issd_defense_approach import pair


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def audit(root, state):
    comparison = pair(root / 'A', root / 'NEUTRAL', 'Right')
    frames, events = {}, {}
    for button in ('A', 'NEUTRAL'):
        directory = root / button
        trace_paths = list(directory.glob('issd-auto-probe-*.jsonl'))
        if len(trace_paths) != 1:
            raise ValueError('Expected one input trace')
        trace = read(trace_paths[0])
        for kind, address, value in [('synthetic_foul_setting', 0x1e50, 0), ('synthetic_referee', 0x1e58, 0)]:
            marks = [row for row in trace if row.get('type') == kind]
            if len(marks) != 1 or marks[0]['address'] != address or marks[0]['value'] != value:
                raise ValueError('Missing synthetic override')
        rows = read(directory / 'defense-opponent.jsonl')
        frames[button] = {r['frame']: r for r in rows if r['type'] == 'frame_end'}
        events[button] = [r for r in rows if r['type'] == 'restart']
        if set(frames[button]) != set(range(4274, 5001)):
            raise ValueError('Incomplete replay window')
    a, n = frames['A'], frames['NEUTRAL']
    for frame in range(4274, comparison['first_input_frame']):
        for key in ('player', 'opponent', 'ball', 'phase', 'phase_c2', 'restart_c4', 'restart_c6', 'selected_11e8', 'link_a6'):
            if a[frame][key] != n[frame][key]:
                raise ValueError(f'Baseline mismatch {frame} {key}')
    expected = ['restart_initialize', 'restart_case_3', 'restart_prepare', 'restart_select_actor', 'restart_actor_selected', 'restart_set_phase_4']
    if [e['site'] for e in events['A']] != expected or events['NEUTRAL']:
        raise ValueError('Unexpected restart route')
    chosen = events['A'][4]
    if chosen['frame'] != 4281 or chosen['restart_c4'] != 0xf00 or chosen['restart_c6'] != 0x1900 or chosen['selected_11e8'] != 0x1200 or chosen['xreg'] != 0x1200:
        raise ValueError('Unexpected selected player')
    if any(a[f]['phase'] != 4 or a[f]['phase_c2'] != 4 or a[f]['selected_11e8'] != 0x1200 for f in range(4282, 5001)):
        raise ValueError('Unexpected phase or selected player')
    if any(n[f]['phase'] or n[f]['foul_00ba'] for f in n):
        raise ValueError('Unexpected control phase')
    return {'schema':'issd-foul-restart-paired/v1', 'declared_state_sha256':sha(state),
            'baseline_samples':comparison['baseline_samples'], 'first_input_frame':comparison['first_input_frame'],
            'action_probe_sha256':sha(root/'A'/'defense-opponent.jsonl'), 'neutral_probe_sha256':sha(root/'NEUTRAL'/'defense-opponent.jsonl'),
            'synthetic_foul_setting':0, 'synthetic_referee':0, 'hook_events':events['A'],
            'observation_window':[4274,5000], 'phase_4_window':[4282,5000],
            'samples':{str(f):{k:a[f][k] for k in ('phase','phase_c2','restart_c4','restart_c6','restart_ca','restart_ce','selected_11e8','link_a6','ball')} for f in (4280,4281,4282,4306,4377,4473,5000)},
            'limitations':['Isolated replay with synthetic referee and foul-setting RAM overrides; ROM and save state are unchanged.',
                'One DF7F contact; selection, phase and restart are not generalized to all fouls.',
                'The replay contains no later deliberate kick input; it does not establish that the free kick was taken.',
                'Matching logged fields before the action does not establish equality of all hidden state.',
                'Screen ball coordinates and CA/CE have not been shown to be directly comparable.',
                'Declared state identity is not authenticated by the trace.']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('root',type=Path); p.add_argument('--state',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    args=p.parse_args(); result=audit(args.root,args.state)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('foul restart pair: OK, selected 0x1200, observed through frame 5000')
