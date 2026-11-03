"""Audit passive selected-P1 route hooks against neutral replay samples."""
import argparse
import hashlib
import json
from pathlib import Path

from compare_issd_action_trials import has_extended, load, signature


def read_hook(path):
    raw = path.read_bytes()
    return [json.loads(line) for line in raw.splitlines() if line.strip()], hashlib.sha256(raw).hexdigest()


def audit(root):
    trials = {}
    for name in ('A', 'B', 'NEUTRAL'):
        directory = root / name
        traces = list(directory.glob('issd-auto-probe-*.jsonl'))
        if len(traces) != 1:
            raise ValueError(f'{name}: expected exactly one driver trace')
        data = load(traces[0])
        hooks, hook_hash = read_hook(directory / 'defense-route.jsonl')
        trials[name] = (data, hooks, hook_hash)
    neutral = trials['NEUTRAL'][0]['samples']
    report = {}
    for name, mask in [('A', 0x80), ('B', 0x8000)]:
        data, hooks, hook_hash = trials[name]
        samples = data['samples']
        before = sorted(t for t in set(samples) & set(neutral) if 0 <= t < 480)
        coverage = any(set(range(parity, 480, 2)) <= set(before) for parity in (0, 1))
        extended = all(has_extended(rows[t]) for rows in (samples, neutral) for t in before)
        matches = all(signature(samples[t], True) == signature(neutral[t], True) for t in before)
        buttons = all(t in samples and t in neutral and samples[t]['held_p1'] == mask and
                      neutral[t]['held_p1'] == 0 for t in range(480, 486))
        if not (coverage and before and extended and matches and buttons):
            raise ValueError(f'{name}: baseline or input proof failed')
        frame = samples[480]['frame'] - 1
        window = [r for r in hooks if frame <= r['frame'] <= frame + 15]
        neutral_hooks = trials['NEUTRAL'][1]
        if [r for r in hooks if r['frame'] < frame] != [r for r in neutral_hooks if r['frame'] < frame]:
            raise ValueError(f'{name}: hook baseline differs')
        if not any(r['site'] == 'entry_9fed' and r['frame'] == frame for r in window):
            raise ValueError(f'{name}: action entry missing at expected frame')
        if any(r['site'] == 'entry_9fed' and r['frame'] == frame for r in neutral_hooks):
            raise ValueError(f'{name}: neutral has the same entry')
        report[name] = {'driver_sha256': data['sha256'], 'hook_sha256': hook_hash,
                        'baseline_samples': len(before), 'first_input_frame': frame,
                        'hook_baseline_matches': True, 'input_mask': mask, 'events': window}
    return {'schema': 'issd-defense-route-probe/v1', 'trials': report,
            'neutral_driver_sha256': trials['NEUTRAL'][0]['sha256'],
            'neutral_hook_sha256': trials['NEUTRAL'][2],
            'limitations': ['Only logged baseline fields are compared.',
                            'Trace input frame is derived from the first post-frame sample.',
                            'Hooks observe the selected actor, not every actor.',
                            'Calls alone do not prove collision acceptance or action semantics.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('audited:', ', '.join(result['trials']))
