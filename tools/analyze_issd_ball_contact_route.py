"""Validate the observed opposing-actor ball response against ROM and replay."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load


def analyze(rom, trace, neutral):
    header = len(rom) % 0x8000
    checks = ((0x23ab7, 'ad3004c90200d03cad6c04c90a00b034acc800a59ad99a00f02a'),
              (0x2f06e, 'a560890080d013'), (0x2f0d3, 'a201004cbff8'))
    if header not in (0, 512) or any(rom[header+o:header+o+len(bytes.fromhex(h))] != bytes.fromhex(h) for o, h in checks):
        raise ValueError('ROM contact route differs')
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay baseline or inputs differ')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    sequence = ('84BA6F', '84BAA8', '84BAB7', '84BAF6', '85F06E', '85F088', '85F0D3', '85F8BF', '85F8D6', '8394EB')
    registered = {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}
    if not set(sequence) <= registered:
        raise ValueError('Missing execution hooks')
    events = [r for r in rows if r.get('type') == 'ball_update_execution' and r['step']-action['trigger'] == 493 and r['dp'] in (0, 0x0f00)]
    cursor = iter(events)
    selected = []
    for name in sequence:
        event = next((r for r in cursor if r['address'] == name), None)
        if event is None:
            raise ValueError(f'Missing or out-of-order callback {name}')
        selected.append(event)
    branch = selected[2]
    if not (branch['ball_type'] == 2 and branch['ball_age'] < 10 and branch['actor_team'] != branch['ref_c8_team']
            and branch['actor_field60'] & 0x8000 and selected[-1]['scratch_00'] == 1):
        raise ValueError('Recorded branch conditions differ')
    return {'schema': 'issd-ball-contact-route/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'sources': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace, neutral)],
            'baseline_samples': proof['before_compared'], 'baseline_mismatches': proof['before_mismatch_count'],
            'elapsed': 493, 'events': selected,
            'limitations': ['Callbacks are pre-instruction; route is one scenario.',
                            'Entry into 84:BA6F and sporting meaning of this response remain unresolved.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path); p.add_argument('trace', type=Path); p.add_argument('neutral', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.rom.read_bytes(), a.trace, a.neutral)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Validated {len(result['events'])} ordered callbacks")
