"""Audit eight independently paired local slide captures; no graphics are exported."""
import argparse
import json
from pathlib import Path
from audit_issd_slide_timing_geometry import audit
from compare_issd_action_trials import load

DIRECTIONS = ('Up', 'UpRight', 'Right', 'DownRight', 'Down', 'DownLeft', 'Left', 'UpLeft')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--analysis', type=Path, default=Path('analysis'))
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    reports = {}
    for name in DIRECTIONS:
        root = args.analysis / ('slide-upright-paired/A' if name == 'UpRight' else 'slide-direction-paired/A/' + name)
        control = args.analysis / ('slide-upright-paired/neutral' if name == 'UpRight' else 'slide-direction-control-graphics/' + name)
        action = load(next(root.glob('issd-auto-probe-*.jsonl')))['samples'][480]['held_p1']
        neutral = load(next(control.glob('issd-auto-probe-*.jsonl')))['samples'][480]['held_p1']
        if action ^ neutral != 0x80:
            raise ValueError(f'{name}: inputs differ beyond action button')
        report = audit(root, control, args.rom, args.state, action, neutral)
        if any(f['direct_mismatches'] != f['same_as_control'] for f in report['frames']):
            raise ValueError(f'{name}: unexplained screenshot pixels')
        reports[name] = report
        print(name, len(report['frames']), 'poses verified')
    args.output.write_text(json.dumps({'schema': 'issd-slide-direction-captures/v1', 'directions': reports}, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
