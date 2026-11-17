"""Compare captured World Series sorter inputs and outputs, without naming their semantics."""
import argparse
import hashlib
import json
from pathlib import Path


def key(record, offset, selected):
    return ((record & 0x003f) << 1) | ((record & 0x3f00) << 1) | (offset == selected)


def audit(path):
    raw = path.read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete capture')
    result = []
    for entry in (h for h in hooks if h['site'] == 'ranking_input'):
        frame = entry['frame']
        records, selected = entry['records'], entry['selected']
        stores = [h for h in hooks if h['site'] == 'ranking_store' and h['frame'] == frame]
        starts = [h for h in hooks if h['site'] == 'ranking_start' and h['frame'] == frame]
        ends = [h for h in hooks if h['site'] == 'ranking_end' and h['frame'] == frame]
        if len(records) != 36 or len(starts) != 1 or len(ends) != 1 or [s['x'] for s in stores] != list(range(0, 72, 2)):
            raise ValueError('Incomplete sorter invocation')
        offsets = [s['y'] for s in stores]
        if sorted(offsets) != list(range(0, 72, 2)):
            raise ValueError('Not a permutation')
        keys = [key(records[offset // 2], offset, selected) for offset in offsets]
        if keys != sorted(keys, reverse=True):
            raise ValueError('Observed ordering differs from descending key')
        result.append({'frame': frame, 'direct_page': starts[0]['d'], 'selected_offset': selected,
                       'records': records, 'ordered_offsets': offsets, 'ordered_keys': keys})
    if not result:
        raise ValueError('No sorter inputs captured')
    return {'schema': 'issd-world-series-sort-keys/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'invocations': result, 'limits': ['Inputs and outputs were captured under synthetic match interventions.',
            'Bit fields and selected offset have not been assigned sports semantics.',
            'Equal-key ordering is not asserted.', 'The ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('hooks', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK: descending keys confirmed for', len(result['invocations']), 'captured invocations')
