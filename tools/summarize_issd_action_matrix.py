"""Summarize paired button trials without naming their gameplay semantics."""
import argparse
import hashlib
import json
from pathlib import Path

from compare_issd_action_trials import compare, load, timeline_row

MASKS = {'A': 0x80, 'B': 0x8000, 'X': 0x40, 'Y': 0x4000}


def summarize_trial(button, action, neutral):
    comparison = compare(action, neutral, MASKS[button])
    eligible = (comparison['baseline_matches_observed_fields'] and
                comparison['p2_action_input_confirmed'] and
                comparison['p2_control_neutral_in_action_window'])
    return {
        'button': button, 'mask': MASKS[button],
        'baseline_observed_fields_match': comparison['baseline_matches_observed_fields'],
        'baseline_samples': comparison['before_compared'],
        'button_confirmed': comparison['p2_action_input_confirmed'],
        'control_neutral_confirmed': comparison['p2_control_neutral_in_action_window'],
        'comparison_eligible': eligible,
        'first_ball_record_difference': comparison['first_after_ball_record_difference'] if eligible else None,
        'ball_record_difference_samples': comparison['after_ball_record_difference_count'] if eligible else None,
        'samples': [{'elapsed': elapsed, 'action': timeline_row(action['samples'][elapsed]),
                     'neutral': timeline_row(neutral['samples'][elapsed])}
                    for elapsed in (479, 481, 483, 485, 487)
                    if elapsed in action['samples'] and elapsed in neutral['samples']],
        'source': {k: v for k, v in action.items() if k != 'samples'},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--neutral', required=True, type=Path)
    parser.add_argument('--state', required=True, type=Path, help='Declared local replay state used by the operator')
    for button in MASKS: parser.add_argument('--' + button.lower(), required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    neutral = load(args.neutral)
    result = {'schema': 'issd-action-matrix/v1',
              'declared_state': {'path': args.state.as_posix(),
                                 'sha256': hashlib.sha256(args.state.read_bytes()).hexdigest()},
              'neutral_source': {k: v for k, v in neutral.items() if k != 'samples'},
              'trials': [summarize_trial(button, load(getattr(args, button.lower())), neutral)
                         for button in MASKS],
              'limitations': ['State identity is supplied by the operator; the trace does not authenticate the loaded file.',
                              'Observed field equality is not a comparison of all emulator state.',
                              'Results apply only to this scenario, configuration and sampled frames.',
                              'Physical buttons are remappable; action names and web physics remain unverified.']}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('eligible:', sum(t['comparison_eligible'] for t in result['trials']), '/', len(MASKS))


if __name__ == '__main__': main()
