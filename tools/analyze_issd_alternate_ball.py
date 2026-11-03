"""Extract the observed post-release ball timeline from paired replays."""
import argparse
import json
from pathlib import Path

from compare_issd_action_trials import compare, load


def analyze(action, control):
    proof = compare(action, control, 0x40)
    for key in ('baseline_matches_observed_fields', 'extended_fields_compared',
                'p2_action_input_confirmed', 'p2_control_neutral_in_action_window'):
        if not proof[key]:
            raise ValueError(f'Paired replay does not establish {key}')
    common = set(action['samples']) & set(control['samples'])
    if not set(range(480, 511)) <= common:
        raise ValueError('Missing a frame from the post-action observation window')
    timeline = []
    for step in range(480, 511):
        pair = []
        for replay in (action, control):
            row = replay['samples'][step]
            pair.append({'ball': row['ball'], 'link_a4': row['link_a4'],
                         'link_a6': row['link_a6']})
        timeline.append({'elapsed': step, 'action': pair[0], 'control': pair[1]})
    return {'schema': 'issd-alternate-ball-observation/v1',
            'sources': [{k: v for k, v in replay.items() if k != 'samples'}
                        for replay in (action, control)],
            'comparison': {k: proof[k] for k in ('before_compared', 'before_mismatch_count',
                           'p2_action_held_only_in_action_trial', 'first_after_ball_record_difference')},
            'timeline': timeline,
            'limitations': ['Only the recorded fields and this particular replay were compared.',
                            'Raw 16-bit values and links are not a complete physics model.',
                            'Type transitions do not by themselves identify the sporting action or its cause.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', type=Path)
    parser.add_argument('control', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    result = analyze(load(args.action), load(args.control))
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Compared {result['comparison']['before_compared']} baseline samples and {len(result['timeline'])} consecutive action samples")


if __name__ == '__main__':
    main()
