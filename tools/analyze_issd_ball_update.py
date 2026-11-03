"""Validate and summarize ball-update callbacks in a controlled replay."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import load, compare

HOOKS = ('8390E6', '8391F6', '839240', '83924F', '839264', '83933B', '83941F', '83882A')


def analyze(rom, trace, neutral):
    header = len(rom) % 0x8000
    if header not in (0, 512) or rom[header + 0x190f9:header + 0x190ff] != bytes.fromhex('37914092f691'):
        raise ValueError('Unexpected ROM ball dispatch table')
    action = load(trace)
    check = compare(action, load(neutral), 0x40)
    if not all(check[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay comparison failed')
    raw = trace.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    registered = {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}
    if not set(HOOKS) <= registered:
        raise ValueError('Missing execution hooks')
    events = [{**r, 'elapsed': r['step'] - action['trigger']} for r in rows if r.get('type') == 'ball_update_execution']
    for elapsed, address, kind in ((487, '8391F6', 2), (493, '839240', 1), (501, '839264', 1)):
        if not any(e['elapsed'] == elapsed and e['address'] == address and e['ball_type'] == kind for e in events):
            raise ValueError('Expected observed update missing')
    return {'schema': 'issd-ball-update-observation/v1',
            'rom_sha256': hashlib.sha256(rom).hexdigest(), 'dispatch_offset_unheadered': '0x190F9',
            'sources': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace, neutral)],
            'baseline_samples': check['before_compared'], 'baseline_mismatches': check['before_mismatch_count'],
            'events': events,
            'limitations': ['Callbacks are before instructions and do not identify the writer of type changes.',
                            'This replay and observed fields do not establish general ball physics.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path); p.add_argument('trace', type=Path); p.add_argument('neutral', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.rom.read_bytes(), a.trace, a.neutral)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Validated {len(result['events'])} callbacks")
