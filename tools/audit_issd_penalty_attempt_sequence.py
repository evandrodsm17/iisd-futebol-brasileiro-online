"""Audit one captured penalty sequence; D values identify this trace only."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(path):
    raw = path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    if events[0].get('site') != 'session_start' or events[-1].get('site') != 'session_end':
        raise ValueError('Incomplete trace')
    checks = [(i, e) for i, e in enumerate(events) if e.get('site') == 'penalty_check']
    actual = [(i, e) for i, e in checks if e['d'] != 0x1500]
    if len(checks) != 55 or len(actual) != 20:
        raise ValueError('Unexpected captured check sequence')
    attempts, previous = [], [0, 0]
    for n, (index, event) in enumerate(actual):
        if (event['side'], event['round']) != ((n % 2) * 2, n // 2):
            raise ValueError('Unexpected native side/round ordering')
        score = [event['penalty_home'], event['penalty_away']]
        delta = [score[i] - previous[i] for i in (0, 1)]
        expected = [0, 0]; expected[n % 2] = 1
        if delta not in ([0, 0], expected):
            raise ValueError('Unexpected counter change')
        same_frame = [e for e in events if e.get('frame') == event['frame']]
        increments = [e for e in same_frame if e.get('site') == 'penalty_increment']
        if len(increments) != (1 if delta == expected else 0):
            raise ValueError('Counter increment mismatch')
        if increments and [increments[0]['penalty_home'], increments[0]['penalty_away']] != previous:
            raise ValueError('Increment input mismatch')
        end = actual[n+1][0] if n+1 < len(actual) else len(events)
        winner = any(e.get('site') == 'penalty_winner' and e.get('frame') == event['frame'] for e in events[index+1:end])
        attempts.append({'frame': event['frame'], 'native_side': event['side'], 'round': event['round'],
                         'before': previous, 'after': score, 'increment_observed': bool(increments),
                         'winner_branch_after_check': winner})
        previous = score
    prelim = sum(e.get('site') == 'penalty_winner' and e['d'] == 0x1500 for e in events)
    if previous != [8, 7] or sum(a['increment_observed'] for a in attempts) != 15 or prelim != 6 or sum(a['winner_branch_after_check'] for a in attempts) != 1:
        raise ValueError('Unexpected captured result')
    return {'schema': 'issd-penalty-attempt-sequence/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'attempts': attempts, 'preliminary_winner_branches': prelim,
            'limitations': ['One synthetic match with automated controls, accelerated clocks and altered regulation score.',
                            'Direct-page values distinguish these observed calls only, not a general classifier.',
                            'Counter changes and same-frame hooks associate outcomes in this trace; cause and full kick timing remain unproven.',
                            'Native sides and round fields are not yet mapped to web player controls.',
                            'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = audit(args.trace)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: {len(result['attempts'])} observed checks; {result['preliminary_winner_branches']} preliminary winner branches")
