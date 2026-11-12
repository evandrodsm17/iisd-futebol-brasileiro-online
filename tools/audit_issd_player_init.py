"""Compare paired native player-initialization hooks from two startup replays."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def load(path):
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    if len(rows) != 44:
        raise ValueError('Expected 22 paired player initializations')
    pairs = []
    for before, after in zip(rows[::2], rows[1::2]):
        if before['site'] != 'before' or after['site'] != 'after':
            raise ValueError('Missing or misordered hooks')
        if after['frame'] - before['frame'] not in (0, 1) or any(before[k] != after[k] for k in ('actor', 'record', 'raw', 'extra')):
            raise ValueError('Initialization pair does not match')
        raw_byte, extra = before['raw'], before['extra']
        if raw_byte >> 4 > 9 or extra not in range(5):
            raise ValueError('Outside audited arithmetic domain')
        delta = min(0, 2 * extra - 4)
        if (after['limit_low'], after['delay_low']) != (max(0, (raw_byte & 15) + delta), min(9, 9 - (raw_byte >> 4) - delta)):
            raise ValueError('Unexpected initialized values')
        pairs.append((before, after))
    return raw, pairs


def audit(baseline_path, patched_path):
    baseline_raw, baseline = load(baseline_path)
    patched_raw, patched = load(patched_path)
    changed = []
    states = collections.Counter()
    for (before, after), (modified, modified_after) in zip(baseline, patched):
        if any(before[k] != modified[k] for k in ('frame', 'actor', 'record', 'original', 'extra')):
            raise ValueError('Replay preparation diverged')
        if before['raw'] != before['original']:
            raise ValueError('Baseline was modified')
        states[before['extra']] += 1
        if modified['raw'] != before['raw']:
            changed.append({'actor': before['actor'], 'record': before['record'], 'extra': before['extra'],
                            'before_raw': before['raw'], 'patched_raw': modified['raw'],
                            'before_fields': {'limit_low': after['limit_low'], 'delay_low': after['delay_low']},
                            'patched_fields': {'limit_low': modified_after['limit_low'], 'delay_low': modified_after['delay_low']}})
        elif (after['limit_low'], after['delay_low']) != (modified_after['limit_low'], modified_after['delay_low']):
            raise ValueError('Untouched actor fields differ')
    if len(changed) != 1 or changed[0] != {'actor': 0x1a00, 'record': 0x3f2c, 'extra': 3,
                                            'before_raw': 0x77, 'patched_raw': 0x93,
                                            'before_fields': {'limit_low': 7, 'delay_low': 2},
                                            'patched_fields': {'limit_low': 3, 'delay_low': 0}}:
        raise ValueError('Unexpected intervention')
    return {'schema': 'issd-player-init-replay/v1', 'emulator': 'BizHawk 2.11, bsnes',
            'baseline_sha256': hashlib.sha256(baseline_raw).hexdigest(),
            'patched_sha256': hashlib.sha256(patched_raw).hexdigest(),
            'paired_actors': len(baseline), 'unmodified_actors': len(baseline) - len(changed),
            'extra_state_counts': dict(sorted(states.items())), 'intervention': changed[0],
            'limits': ['A single synthetic byte was changed in emulated RAM immediately before initialization; ROM and disk savestate were not modified.',
                       'Two controlled startup replays; only the sampled fields and hook contexts were compared.',
                       'This does not prove the mapping of a web-edited roster or the end-to-end browser physics.',
                       'Native meaning of extra runtime byte is not established.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for arg in ('baseline', 'patched', 'output'):
        parser.add_argument(arg, type=Path)
    a = parser.parse_args()
    result = audit(a.baseline, a.patched)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: 22 initializations in each replay; only intended player changed')
