"""Audit fractional position changes in paired directional replays."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def word32(high, low):
    return (high << 16) | low


def signed32(value):
    return ((value + 0x80000000) & 0xffffffff) - 0x80000000


def audit(path):
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    groups = collections.defaultdict(list)
    for row in rows:
        if row.get('type') == 'error':
            raise ValueError('Replay reported an error')
        groups[(row['case'], row['controller'])].append(row)
    names = ('neutral', 'right', 'left', 'up', 'down')
    if len(rows) != 1200 or set(groups) != {(n, c) for n in names for c in (1, 2)}:
        raise ValueError('Incomplete paired replays')
    summaries = {}
    for name in names:
        samples = groups[(name, 2)]
        if [s['step'] for s in samples] != list(range(1, 121)) or len({s['actor'] for s in samples}) != 1:
            raise ValueError('Controlled actor or step sequence changed')
        stable = []
        for a, b in zip(samples, samples[1:]):
            if a['state'] != 32 or b['state'] != 32 or a['dir'] != b['dir']:
                continue
            dx = signed32(word32(b['x'], b['x_frac']) - word32(a['x'], a['x_frac']))
            dz = signed32(word32(b['z'], b['z_frac']) - word32(a['z'], a['z_frac']))
            velocity_a = [signed32(word32(a['vx'], a['vx_frac'])), signed32(word32(a['vz'], a['vz_frac']))]
            velocity_b = [signed32(word32(b['vx'], b['vx_frac'])), signed32(word32(b['vz'], b['vz_frac']))]
            stable.append({'delta': [dx, dz], 'previous_velocity': velocity_a, 'current_velocity': velocity_b,
                           'level': b['level'], 'direction': b['dir']})
        counts = collections.Counter(tuple(item['delta']) for item in stable)
        residuals = collections.Counter(tuple(item['delta'][i] - item['current_velocity'][i] for i in (0, 1)) for item in stable)
        summaries[name] = {'actor': samples[0]['actor'], 'stable_pairs': len(stable),
                           'matches_previous_velocity': sum(item['delta'] == item['previous_velocity'] for item in stable),
                           'matches_current_velocity': sum(item['delta'] == item['current_velocity'] for item in stable),
                           'levels': sorted({item['level'] for item in stable}),
                           'directions': sorted({item['direction'] for item in stable}),
                           'common_delta_16_16': [{'delta': list(delta), 'count': count} for delta, count in counts.most_common(5)],
                           'common_delta_minus_velocity_16_16': [{'residual': list(delta), 'count': count} for delta, count in residuals.most_common(5)]}
    if not all(summaries[n]['stable_pairs'] >= 20 for n in ('right', 'left', 'up')):
        raise ValueError('Insufficient stable directional pairs')
    return {'schema': 'issd-free-movement-paired/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'emulator': 'BizHawk 2.11, bsnes', 'preparation': 'same shot-start state; X held 2 steps then neutral 88 steps; five 120-step trials',
            'case_summaries': summaries,
            'limits': ['State 0x20 is used as an observed stable selector, not a universal movement classification.',
                       'Frame-end deltas may include unrelated updates; matching arithmetic is not proof of one specific writer.',
                       'One state, one selected actor and one preparation; not a universal speed calibration.',
                       'Native units and frames are not yet converted to browser units.',
                       'ROM, savestate and raw traces remain local.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('trace', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    report = audit(a.trace)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: paired trials and 16.16 deltas audited')
