"""Compare the E8B0 model with paired pre-return execution callbacks."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load
from issd_ball_contact_geometry import contact_carry


def analyze(rom, trace, neutral):
    code = bytes.fromhex('adfa113032a53ed02ea568f02ca51038ed1004c91800b01fa90c00186508ed080438e91800b00da9080018650ced0c0438e910006018603860acc800a59ad99a00f0caad100438e510f00710eac9d0ff90e5a90e00186508ed080438e91c00b00da90a0018650ced0c0438e91400c22060')
    header = len(rom) % 0x8000
    if header not in (0, 512) or rom[header+0x268b0:header+0x268b0+len(code)] != code:
        raise ValueError('Unexpected E8B0 routine')
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared', 'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay baseline or inputs differ')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    names = {'84E8B0', '84E8E4', '84E8E7', '84E91E'}
    registered = {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}
    if not names <= registered:
        raise ValueError('Missing geometry hooks')
    pending = {}
    results = []
    for row in rows:
        if row.get('type') != 'ball_update_execution' or row['address'] not in names:
            continue
        key = (row['step'], row['dp'])
        if row['address'] == '84E8B0':
            if key in pending:
                raise ValueError('Nested or repeated entry before return')
            pending[key] = row
        elif key in pending:
            entry = pending.pop(key)
            expected = contact_carry(*(entry[k] for k in ('actor_x', 'actor_y', 'actor_z', 'x_pos', 'y_pos', 'z_pos',
                                      'actor_3e', 'actor_68', 'global_11fa', 'actor_team', 'ref_c8_team')))
            observed = 1 if row['address'] == '84E8E7' else row['carry']
            if observed not in (0, 1) or observed != expected:
                raise ValueError(f'Carry mismatch or unavailable at step {row["step"]}')
            results.append({'elapsed': row['step']-action['trigger'], 'actor': row['dp'],
                            'entry': entry, 'return_address': row['address'], 'carry': observed})
    if pending or not results:
        raise ValueError('Unpaired or missing geometry callbacks')
    return {'schema': 'issd-ball-contact-geometry/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'sources': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace, neutral)],
            'baseline_samples': proof['before_compared'], 'comparisons': len(results), 'mismatches': 0,
            'results': results, 'limitations': ['Only observed calls were compared; unvisited branches require separate validation.',
                        'Callbacks do not establish the sporting meaning of contact.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path); p.add_argument('trace', type=Path); p.add_argument('neutral', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.rom.read_bytes(), a.trace, a.neutral)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(f"Matched {result['comparisons']} geometry returns")
