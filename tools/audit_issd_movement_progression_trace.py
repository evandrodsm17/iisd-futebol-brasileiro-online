"""Compare paired pre-instruction hooks with 80:DD9F's word operations."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def audit(path):
    raw = path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    if any(e.get('type') != 'hook' for e in events):
        raise ValueError('Incomplete replay or unsupported record')
    pending, gaps, last = {}, collections.Counter(), {}
    counts = collections.Counter()
    actor_counts = collections.Counter()
    high_limit = 0
    observed_delay_low = collections.Counter()
    for e in events:
        counts[e['site']] += 1
        key = e['actor']
        if e['site'] == 'entry':
            if key in pending:
                raise ValueError('Unpaired earlier entry')
            pending[key] = e
            actor_counts[key] += 1
            if key in last:
                gaps[e['step'] - last[key]] += 1
            last[key] = e['step']
            high_limit += bool(e['limit'] & 0xff00)
            observed_delay_low[e['delay'] & 0xff] += 1
        elif e['site'] in ('carry', 'increment'):
            before = pending.pop(key, None)
            if before is None or before['step'] != e['step']:
                raise ValueError('Unmatched return hook')
            timer = (before['timer'] - 1) & 0xffff
            increment = bool(timer & 0x8000) and before['level'] < before['limit']
            expected = {'site': 'increment' if increment else 'carry',
                        'timer': before['delay'] & 255 if increment else timer,
                        'level': (before['level'] + 1) & 0xffff if increment else before['level'],
                        'limit': before['limit'], 'delay': before['delay']}
            if any(e[k] != value for k, value in expected.items()):
                raise ValueError(f'Unexpected output at {key:x}, step {e["step"]}')
        elif e['site'] != 'project':
            raise ValueError('Unknown hook')
    if pending or counts['entry'] == 0 or counts['increment'] == 0:
        raise ValueError('Insufficient paired observations')
    return {'schema': 'issd-movement-progression-replay/v1',
            'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'emulator': 'BizHawk 2.11, bsnes core, original 2.11 savestate',
            'trial': '240 emulated steps, player 2 Right held, player 1 neutral',
            'events': dict(counts), 'actors_with_entry': len(actor_counts),
            'entries_with_nonzero_limit_high_byte': high_limit,
            'delay_low_counts': dict(sorted(observed_delay_low.items())),
            'consecutive_entry_step_gaps_by_actor': dict(sorted(gaps.items())),
            'limits': ['Single saved scenario and direction; input does not prove actor control or free movement.',
                       'Pairs are hooks during one emulated step, not a full account of updates outside these hooks.',
                       'Gaps measure consecutive observed calls per actor, not an unconditional frequency.',
                       'No ROM, state or raw trace is distributed.',
                       'This validates observed inputs and outputs, not the native-to-web scale or behavior of other game states.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('trace', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    report = audit(args.trace)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: {report['events']['entry']} entradas pareadas, {report['events']['increment']} incrementos")
