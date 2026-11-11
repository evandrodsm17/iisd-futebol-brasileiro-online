"""Audit frame-end horizontal velocity changes in the local type-5 sweep."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(trace):
    raw = trace.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    hooks = [r for r in rows if r['type'] == 'hook' and r['site'] == '85F89B']
    if len(hooks) != 15 or {h['y'] for h in hooks} != set(range(12)):
        raise ValueError('Incomplete charge sweep')
    keys = ('vx', 'vxFrac', 'vy', 'vyFrac')
    unchanged = 0
    changes = []
    for hook in hooks:
        frames = [r for r in rows if r['type'] == 'frame' and r['trial'] == hook['trial'] and r['step'] >= hook['step']]
        for a, b in zip(frames, frames[1:]):
            if b['step'] != a['step'] + 1:
                raise ValueError('Missing frame')
            if a['ballType'] != 5 or b['ballType'] != 5 or a['carrier'] != 0 or b['carrier'] != 0:
                continue
            before = [a[k] for k in keys]
            after = [b[k] for k in keys]
            if before == after:
                unchanged += 1
            else:
                changes.append({'trial': hook['trial'], 'parameter': hook['y'],
                                'before_step': a['step'], 'after_step': b['step'],
                                'horizontal_before': before, 'horizontal_after': after,
                                'vertical_before': [a['vz'], a['vzFrac']],
                                'vertical_after': [b['vz'], b['vzFrac']]})
    if unchanged != 453 or len(changes) != 2:
        raise ValueError('Unexpected number of transitions')
    for change in changes:
        if change['horizontal_before'] != [65528, 12288, 65535, 47616] or change['horizontal_after'] != [65529, 10752, 65535, 49856]:
            raise ValueError('Unexpected horizontal change')
        if not (change['vertical_before'][0] < 0x8000 <= change['vertical_after'][0]):
            raise ValueError('Vertical velocity did not reverse in the recorded frames')
    return {'schema': 'issd-type5-horizontal-flight/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'horizontal_word_order': ['vx_integer', 'vx_fraction', 'vy_integer', 'vy_fraction'],
            'unchanged_transitions': unchanged, 'changes': changes,
            'limits': ['Frame-end samples from one saved state, actor, direction and weather.',
                       'No height or impact hook was recorded, so the exact cause of the two changes is not proven.',
                       'Adjacent frames may contain zero, one or several native updates.',
                       'No general rule for other angles, weather, impacts or web scale is established.',
                       'The local trace and ROM are not distributed.']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = audit(args.trace)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: {report['unchanged_transitions']} unchanged and {len(report['changes'])} changed transitions")


if __name__ == '__main__':
    main()
