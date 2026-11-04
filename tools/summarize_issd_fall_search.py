"""Summarize observed fall-state candidates in isolated BizHawk probe logs.

This identifies frames for further paired capture; it does not validate sprites
or prove which action caused a fall.
"""
import argparse
import json
from pathlib import Path
from compare_issd_action_trials import load


def summarize(path, start=420, end=479):
    data = load(path)
    samples = data['samples']
    missing = [t for t in range(start, end) if t not in samples]
    hits = []
    for elapsed in range(start, end):
        row = samples.get(elapsed)
        if row is None:
            continue
        for actor in row.get('actors', []):
            if actor['state'] == 0x328:
                hits.append({'elapsed': elapsed, 'frame': row['frame'],
                    'actor': actor['address'], 'direction': actor['direction'],
                    'descriptor': actor['descriptor'], 'link_a6': row['link_a6']})
    return {'path': data['path'], 'sha256': data['sha256'], 'window': [start, end],
            'missing_elapsed': missing, 'fall_state_samples': hits}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('directory', type=Path)
    p.add_argument('--start', type=int, default=420)
    p.add_argument('--end', type=int, default=479, help='exclusive')
    args = p.parse_args()
    if args.start >= args.end:
        p.error('start must be before end')
    paths = sorted(args.directory.glob('*/issd-auto-probe-*.jsonl'))
    if not paths:
        p.error('no probe logs found in immediate subdirectories')
    print(json.dumps({'schema': 'issd-fall-search-summary/v1',
        'limitations': ['Candidate observations only; paired capture and graphical validation are required.',
                        'A missing sampled frame prevents ruling out a fall in that frame.'],
        'trials': [summarize(path, args.start, args.end) for path in paths]}, indent=2))


if __name__ == '__main__':
    main()
