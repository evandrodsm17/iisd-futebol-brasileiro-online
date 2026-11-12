"""Correlate frame-end motion residuals with the two native reference words."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def signed(value, bits):
    return ((value + (1 << (bits - 1))) % (1 << bits)) - (1 << (bits - 1))


def audit(path, baseline):
    raw = path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    prior = [json.loads(line) for line in baseline.read_bytes().splitlines()]
    if len(events) != 1200 or len(prior) != len(events):
        raise ValueError('Incomplete paired replay')
    for current, old in zip(events, prior):
        if any(current.get(k) != value for k, value in old.items()):
            raise ValueError('Replay diverged from previous capture')
    groups = collections.defaultdict(list)
    for e in events:
        groups[(e['case'], e['controller'])].append(e)
    report = {}
    for case in ('neutral', 'right', 'left', 'up', 'down'):
        rows = groups[(case, 2)]
        if len(rows) != 120 or len({r['actor'] for r in rows}) != 1:
            raise ValueError('Unexpected actor or frame count')
        exact = corrected_x = corrected_both = 0
        residuals = collections.Counter()
        total = 0
        for a, b in zip(rows, rows[1:]):
            if a['state'] != 32 or b['state'] != 32 or a['dir'] != b['dir']:
                continue
            if b['step'] != a['step'] + 1:
                raise ValueError('Nonconsecutive samples')
            pos = lambda e, k, f: (e[k] << 16) | e[f]
            dx = signed(pos(b, 'x', 'x_frac') - pos(a, 'x', 'x_frac'), 32)
            dz = signed(pos(b, 'z', 'z_frac') - pos(a, 'z', 'z_frac'), 32)
            vx = signed(pos(b, 'vx', 'vx_frac'), 32)
            vz = signed(pos(b, 'vz', 'vz_frac'), 32)
            rx, rz = dx - vx, dz - vz
            refx = signed(b['camera_x'] - a['camera_x'], 16) * 65536
            refz = signed(b['camera_z'] - a['camera_z'], 16) * 65536
            total += 1
            exact += (rx, rz) == (0, 0)
            corrected_x += rx == -refx
            corrected_both += (rx, rz) == (-refx, -refz)
            residuals[(rx, rz, refx, refz)] += 1
        report[case] = {'stable_pairs': total, 'exact_velocity_pairs': exact,
                        'horizontal_residual_equals_negative_reference_delta': corrected_x,
                        'both_residuals_equal_negative_reference_deltas': corrected_both,
                        'common_residual_and_reference_changes': [
                            {'residual_x': k[0], 'residual_z': k[1], 'reference_x': k[2], 'reference_z': k[3], 'count': n}
                            for k, n in residuals.most_common(5)]}
    if sum(r['stable_pairs'] for r in report.values()) != 378 or any(
            r['stable_pairs'] != r['both_residuals_equal_negative_reference_deltas'] for r in report.values()):
        raise ValueError('Reference correlation changed; review replay and interpretation')
    return {'schema': 'issd-movement-camera-residuals/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'baseline_sha256': hashlib.sha256(baseline.read_bytes()).hexdigest(), 'baseline_rows_matching': len(events),
            'cases': report, 'limits': ['One replay state and selected actor; frame-end correlation is not a write trace.',
            'Reference words $0098/$009A may be changed by multiple routines.',
            'State 0x20 is a filter, not a universal movement classification.',
            'ROM, savestate and raw traces are not distributed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for arg in ('trace', 'baseline', 'output'):
        parser.add_argument(arg, type=Path)
    a = parser.parse_args()
    report = audit(a.trace, a.baseline)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: 1,200 matching replay rows; reference correlation audited')
