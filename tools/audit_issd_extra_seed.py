"""Audit the idle-loop writes observed before roster-state generation."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def audit(path):
    raw = path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    writes = [r for r in events if r['site'] == 'seed_write']
    entries = [r for r in events if r['site'] == 'entry' and r['frame'] == 1948]
    if len(entries) != 1 or len(writes) < 100 or any(r['pc'] != 0x8080de or r['d'] != 0 for r in writes):
        raise ValueError('Missing observations or unexpected writer')
    preceding = [r for r in events[:events.index(entries[0])] if r['site'] == 'seed_write']
    if not preceding or preceding[-1]['a'] != entries[0]['seed']:
        raise ValueError('Last observed idle write does not match generator input')
    # Match individual address streams to avoid counting the same bus write twice.
    streams = collections.defaultdict(list)
    for row in writes:
        streams[row['watch']].append(row)
    checked = 0
    for stream in streams.values():
        for a, b in zip(stream, stream[1:]):
            if a['frame'] != b['frame']:
                continue
            if b['a'] != ((a['a'] + b['addend'] + (a['p'] & 1)) & 0xffff):
                raise ValueError('Unexpected idle-loop recurrence')
            checked += 1
    if checked < 100:
        raise ValueError('Insufficient consecutive observations')
    last = preceding[-1]
    return {'schema': 'issd-roster-extra-seed/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'observed_writes': len(writes), 'same_frame_pairs_verified': checked,
            'address_counts': dict(sorted(collections.Counter(r['watch'] for r in writes).items())),
            'last_observed_write': {k: last[k] for k in ('frame', 'pc', 'a', 'p', 'addend')},
            'generator_entry': {k: entries[0][k] for k in ('frame', 'd', 'seed')},
            'limits': ['One automated startup; memory observation was enabled only for frames 1900 through 1948.',
                       'Last observed write is evidence of continuity, not proof of every possible alias or internal write.',
                       'The idle loop depends on CPU scheduling and carry; an online replacement is not established.',
                       'No proof that the gameplay meaning of the generated player state is form or condition.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    a = parser.parse_args()
    report = audit(a.trace)
    a.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: {report['observed_writes']} writes, {report['same_frame_pairs_verified']} verified pairs")
