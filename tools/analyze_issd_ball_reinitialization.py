"""Correlate replayed ball reinitializations with verified ROM instructions."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load


def analyze(rom, trace, neutral):
    header = len(rom) % 0x8000
    if header not in (0, 512):
        raise ValueError('Unsupported ROM header')
    # 85:EECE: LDX #0; JSL 85:F8C5; STX $00A6
    if rom[header + 0x2eece:header + 0x2eed8] != bytes.fromhex('a2000022c5f8858ea600'):
        raise ValueError('Unexpected 85:EECE instructions')
    if rom[header + 0x194eb:header + 0x194f3] != bytes.fromhex('a5008d30048d7604'):
        raise ValueError('Unexpected 83:94EB instructions')
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Paired comparison failed')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete capture')
    required = {'85F8D6', '8394EB', '85EECE'}
    registered = {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}
    if not required <= registered:
        raise ValueError('Missing hooks')
    events = [{**r, 'elapsed': r['step'] - action['trigger']} for r in rows
              if r.get('type') == 'ball_update_execution' and r.get('address') in required]
    for step, address, old, new in ((487, '8394EB', 0, 2), (493, '8394EB', 2, 1), (502, '8394EB', 1, 0)):
        if not any(e['elapsed'] == step and e['address'] == address and e['ball_type'] == old
                   and e['scratch_00'] == new for e in events):
            raise ValueError('Expected reinitialization absent')
    if not any(e['elapsed'] == 502 and e['address'] == '85EECE' and e['dp'] == 0x0f00 for e in events):
        raise ValueError('Expected actor route absent')
    return {'schema': 'issd-ball-reinitialization/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'sources': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace, neutral)],
            'baseline_samples': proof['before_compared'], 'baseline_mismatches': proof['before_mismatch_count'],
            'events': events, 'limitations': ['Callbacks occur before instructions.',
               'The origin of the type-1 initialization and the full contact semantics remain unconfirmed.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path); p.add_argument('trace', type=Path); p.add_argument('neutral', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.rom.read_bytes(), a.trace, a.neutral)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Validated {len(result['events'])} reinitialization callbacks")
