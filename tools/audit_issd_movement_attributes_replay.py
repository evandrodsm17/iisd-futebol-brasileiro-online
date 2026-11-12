"""Audit controlled in-memory changes to effective actor movement fields."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def signed32(v):
    return ((v + 0x80000000) & 0xffffffff) - 0x80000000


def audit(trace_path, reference_path):
    raw = trace_path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    reference_raw = reference_path.read_bytes()
    reference = [json.loads(line) for line in reference_raw.splitlines()]
    if any(r.get('type') == 'error' for r in rows):
        raise ValueError('Replay failed')
    cases = ('baseline', 'limit3', 'limit9', 'delay0', 'delay8')
    setups, frames = {}, collections.defaultdict(list)
    for row in rows:
        if row['type'] == 'setup':
            if row['case'] in setups:
                raise ValueError('Duplicate setup')
            setups[row['case']] = row
        elif row['type'] == 'frame':
            frames[row['case']].append(row)
        else:
            raise ValueError('Unexpected record')
    if set(setups) != set(cases) or set(frames) != set(cases):
        raise ValueError('Incomplete experiment')
    initial = setups['baseline']
    if (initial['old_limit'], initial['old_delay']) != (7, 1538):
        raise ValueError('Unexpected initial effective fields')
    changes = {'baseline': (7, 2), 'limit3': (3, 2), 'limit9': (9, 2), 'delay0': (7, 0), 'delay8': (7, 8)}
    ref = [r for r in reference if r['case'] == 'right_y' and r['controller'] == 2]
    if len(ref) != 120:
        raise ValueError('Missing independent baseline')
    compare_keys = ('step', 'frame', 'actor', 'x', 'x_frac', 'z', 'z_frac', 'vx', 'vx_frac', 'vz', 'vz_frac', 'dir', 'state', 'timer', 'level', 'limit', 'delay')
    for actual, expected in zip(frames['baseline'], ref):
        if any(actual[k] != expected[k] for k in compare_keys) or actual['reference_x'] != expected['camera_x'] or actual['reference_z'] != expected['camera_z']:
            raise ValueError('Baseline diverges from independently recorded replay')
    result = {}
    for name in cases:
        setup, samples = setups[name], frames[name]
        expected_limit, expected_delay = changes[name]
        if (setup['old_limit'], setup['old_delay'], setup['actor']) != (initial['old_limit'], initial['old_delay'], initial['actor']):
            raise ValueError('Preparation differs between scenarios')
        if setup['limit'] != expected_limit or setup['delay'] != ((initial['old_delay'] & 0xff00) | expected_delay):
            raise ValueError('Unexpected synthetic field value')
        if len(samples) != 120 or [r['step'] for r in samples] != list(range(1, 121)) or any(r['actor'] != initial['actor'] or r['selected'] != initial['actor'] for r in samples):
            raise ValueError('Actor selection or frame sequence changed')
        if any(r['limit'] != setup['limit'] or r['delay'] != setup['delay'] for r in samples):
            raise ValueError('Synthetic fields were overwritten')
        running = [r for r in samples if r['state'] == 56 and r['dir'] == 0]
        target = expected_limit
        first_target = next((r['step'] for r in running if r['level'] == target), None)
        steady = [r for r in running if r['level'] == target]
        if not steady or first_target is None:
            raise ValueError('No target-level observations')
        speeds = collections.Counter(signed32((r['vx'] << 16) | r['vx_frac']) for r in steady)
        first, last = samples[0], samples[-1]
        corrected = lambda r: (((r['x'] + r['reference_x']) & 0xffff) << 16) | r['x_frac']
        result[name] = {'effective_limit': setup['limit'], 'effective_delay_low': setup['delay'] & 255,
                        'first_target_level_step': first_target, 'target_level': target,
                        'target_level_samples': len(steady), 'horizontal_velocity_16_16_counts': dict(sorted(speeds.items())),
                        'corrected_horizontal_displacement_16_16': signed32(corrected(last) - corrected(first)),
                        'state_counts': dict(collections.Counter(r['state'] for r in samples))}
    if not (result['limit3']['corrected_horizontal_displacement_16_16'] < result['baseline']['corrected_horizontal_displacement_16_16'] < result['limit9']['corrected_horizontal_displacement_16_16']):
        raise ValueError('Expected limit response was not observed')
    if not (result['delay0']['first_target_level_step'] < result['baseline']['first_target_level_step'] < result['delay8']['first_target_level_step']):
        raise ValueError('Expected delay response was not observed')
    return {'schema': 'issd-movement-attribute-intervention/v1',
            'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'independent_baseline_sha256': hashlib.sha256(reference_raw).hexdigest(),
            'baseline_samples_matched': len(ref), 'actor': initial['actor'], 'cases': result,
            'limits': ['Synthetic intervention changes only effective RAM fields, not player roster or ROM.',
                       'Single actor, initial state, direction and button combination; no general physical calibration.',
                       'The exact mapping from changed editor values through player initialization was not dynamically exercised.',
                       'Reference-corrected displacement assumes frame-end reference correlation already documented.',
                       'ROM, state and raw traces are not distributed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for key in ('trace', 'reference', 'output'):
        parser.add_argument(key, type=Path)
    args = parser.parse_args()
    report = audit(args.trace, args.reference)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: baseline reproduced; five effective-field experiments audited')
