"""Compare natural contact replays with paired neutral-input controls."""
import argparse
import hashlib
import json
from pathlib import Path

from compare_issd_action_trials import has_extended, load, signature


def only_trace(directory):
    traces = list(directory.glob('issd-auto-probe-*.jsonl'))
    if len(traces) != 1:
        raise ValueError(f'{directory}: expected one trace')
    return load(traces[0])


def pair(action_dir, neutral_dir, direction):
    a, n = only_trace(action_dir), only_trace(neutral_dir)
    action, neutral = a['samples'], n['samples']
    common = sorted(set(action) & set(neutral))
    before = [t for t in common if 0 <= t < 480]
    coverage = any(set(range(i, 480, 2)) <= set(before) for i in (0, 1))
    extended = all(has_extended(rows[t]) for rows in (action, neutral) for t in before)
    matches = all(signature(action[t], True) == signature(neutral[t], True) for t in before)
    buttons = all(t in action and t in neutral and action[t]['held_p1'] == 0x80 and
                  neutral[t]['held_p1'] == 0 for t in range(480, 486))
    approach = [t for t in common if 440 <= t < 480]
    approach_confirmed = (len(approach) >= 20 and all(action[t].get('input') == direction and
                          neutral[t].get('input') == direction for t in approach))
    if not (before and coverage and extended and matches and buttons and approach_confirmed):
        raise ValueError(f'{action_dir}: paired baseline or input check failed')
    actor = action[479]['selected_p1']
    first_frame = action[480]['frame'] - 1
    gate_path = action_dir / 'slide-ball-gate.jsonl'
    gate_raw = gate_path.read_bytes()
    events = [json.loads(line) for line in gate_raw.splitlines() if line.strip()]
    gate = [e for e in events if e['actor'] == actor and first_frame <= e['frame'] <= first_frame+40]
    if any(e['synthetic'] for e in gate):
        raise ValueError('Expected passive events')
    def snapshot(row):
        return {key: row[key] for key in ('frame','selected_p1','actor','ball','link_a4','link_a6','held_p1')}
    timeline = [{'elapsed': t, 'action': snapshot(action[t]), 'neutral': snapshot(neutral[t])}
                for t in common if 478 <= t <= 510]
    return {'baseline_samples':len(before), 'approach':direction, 'approach_samples_confirmed':len(approach),
            'input_mask':0x80, 'input_frames_confirmed':6,
            'selected_actor_at_action':actor, 'first_input_frame':first_frame,
            'action_trace_sha256':a['sha256'], 'neutral_trace_sha256':n['sha256'],
            'gate_sha256':hashlib.sha256(gate_raw).hexdigest(), 'gate_events':gate, 'timeline':timeline}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--action-root',type=Path,required=True)
    p.add_argument('--neutral-root',type=Path,required=True)
    p.add_argument('--state',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    result={'schema':'issd-defense-approach/v1',
            'declared_state_sha256':hashlib.sha256(args.state.read_bytes()).hexdigest(),
            'trials':{d:pair(args.action_root/d,args.neutral_root/d,d) for d in ('Right','DownRight')},
            'limitations':['Declared state identity is not authenticated by the emulator trace.',
                           'Comparison covers logged fields, not all hidden state.',
                           'The gate is one step in the action; causality and semantics require further tracing.',
                           'Coordinates are native units, not calibrated browser units.']}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('audited:', ', '.join(result['trials']))
