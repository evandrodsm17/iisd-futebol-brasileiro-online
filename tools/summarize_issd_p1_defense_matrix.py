"""Compare P1 button trials against the same sampled neutral replay."""
import argparse
import hashlib
import json
from pathlib import Path

from compare_issd_action_trials import has_extended, load, signature

MASKS = {'A': 0x80, 'B': 0x8000, 'X': 0x40, 'Y': 0x4000}


def summarize(action, neutral, mask):
    a, n = action['samples'], neutral['samples']
    common = sorted(set(a) & set(n))
    before = [t for t in common if 0 <= t < 480]
    extended = bool(before) and all(has_extended(rows[t]) for rows in (a, n) for t in before)
    mismatches = [t for t in before if signature(a[t], extended) != signature(n[t], extended)]
    coverage = set(range(0, 480, 2)) <= set(before) or set(range(1, 480, 2)) <= set(before)
    inputs = list(range(480, 486))
    confirmed = all(t in a and t in n and a[t].get('held_p1') == mask and
                    n[t].get('held_p1') == 0 for t in inputs)
    eligible = coverage and extended and not mismatches and confirmed
    def snapshot(row):
        return {'held_p1': row.get('held_p1'), 'actor': row.get('actor'),
                'link_a6': row.get('link_a6'), 'ball': row.get('ball')}
    return {'mask': mask, 'baseline_samples': len(before), 'baseline_mismatches': len(mismatches),
            'baseline_coverage': coverage, 'extended_fields_compared': extended,
            'six_input_frames_confirmed': confirmed, 'comparison_eligible': eligible,
            'timeline': [{'elapsed': t, 'action': snapshot(a[t]), 'neutral': snapshot(n[t])}
                         for t in (479, 480, 481, 485, 487, 500)
                         if t in a and t in n],
            'source': {k: v for k, v in action.items() if k != 'samples'}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--neutral', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    for button in MASKS:
        parser.add_argument('--' + button.lower(), type=Path, required=True)
    args = parser.parse_args()
    neutral = load(args.neutral)
    result = {'schema': 'issd-p1-defense-matrix/v1',
              'declared_state': {'path': args.state.as_posix(),
                                 'sha256': hashlib.sha256(args.state.read_bytes()).hexdigest()},
              'neutral_source': {k: v for k, v in neutral.items() if k != 'samples'},
              'trials': {b: summarize(load(getattr(args, b.lower())), neutral, mask)
                         for b, mask in MASKS.items()},
              'limitations': ['The declared state is not authenticated by the trace.',
                              'Only logged fields are compared, not hidden emulator state.',
                              'Results apply to this sampled scenario; button meanings are context-dependent.',
                              'No action semantics or animation are identified by the state alone.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('eligible:', sum(t['comparison_eligible'] for t in result['trials'].values()), '/ 4')


if __name__ == '__main__':
    main()
