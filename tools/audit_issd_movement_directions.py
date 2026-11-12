"""Summarize paired direction trials without assuming uninterrupted movement."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def signed_delta(a, b):
    return ((b - a + 0x8000) & 0xffff) - 0x8000


def audit(path):
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    groups = collections.defaultdict(list)
    for row in rows:
        if row.get('type') == 'error':
            raise ValueError('Replay failed: ' + row.get('detail', 'unknown error'))
        groups[(row['case'], row['controller'])].append(row)
    names = ('neutral', 'right', 'left', 'up', 'down')
    if len(rows) != 1200 or set(groups) != {(n, c) for n in names for c in (1, 2)}:
        raise ValueError('Incomplete direction matrix')
    for key, group in groups.items():
        if [r['step'] for r in group] != list(range(1, 121)):
            raise ValueError(f'Unexpected frame sequence: {key}')
    for controller in (1, 2):
        if len({groups[(n, controller)][0]['actor'] for n in names}) != 1:
            raise ValueError('Initial controlled actor differs between trials')
    report = {}
    for name in names:
        report[name] = {}
        for controller in (1, 2):
            group = groups[(name, controller)]
            start, end = group[0], group[-1]
            actors = sorted({r['actor'] for r in group})
            same_actor = len(actors) == 1
            report[name][str(controller)] = {
                'actors': actors, 'stable_actor': same_actor,
                'first_state': start['state'], 'final_state': end['state'],
                'dominant_states': dict(collections.Counter(r['state'] for r in group).most_common(4)),
                'dominant_directions': dict(collections.Counter(r['dir'] for r in group).most_common(4)),
                'levels_observed': sorted({r['level'] for r in group}),
                'position_delta_first_to_last': [signed_delta(start['x'], end['x']), signed_delta(start['z'], end['z'])] if same_actor else None,
            }
    if report['neutral']['2']['position_delta_first_to_last'] != [0, 0]:
        raise ValueError('Neutral baseline changed; review conclusions')
    if report['right']['2']['position_delta_first_to_last'] == [0, 0] or report['up']['2']['position_delta_first_to_last'] == [0, 0]:
        raise ValueError('Directional trials did not differ from baseline')
    return {'schema': 'issd-movement-direction-paired/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'emulator': 'BizHawk 2.11, bsnes; same original state before each trial',
            'steps_per_trial': 120, 'trials': report,
            'limits': ['Frame-end snapshots only; no execution hooks or exact point of transition.',
                       'Controller record actor selection is observed, not proof of exclusive control.',
                       'States change and level remains zero for player 2; trials do not establish free running speed.',
                       'Positions are native words with wrapping; no native-to-web scale established.',
                       'ROM, savestate and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.trace)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: cinco replays, dois controles e 1.200 amostras')
