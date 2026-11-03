"""Validate one type-1 ball initialization against ROM tables and replay."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load


def analyze(rom, trace, neutral):
    header = len(rom) % 0x8000
    if header not in (0, 512):
        raise ValueError('Unsupported ROM header')
    parameter = rom[header + 0xa378]  # 81:A367 + (type 1 * 16) + parameter 1
    vector = rom[header + 0xa5e7:header + 0xa5eb]  # 81:A5D7 + angle 4 * 4
    if parameter != 40 or vector != bytes.fromhex('280ece05'):
        raise ValueError('Unexpected ROM parameter or vector entries')
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay baseline or inputs differ')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    names = ('839E32', '839E92', '839EC3', '83953F', '839722', '839750', '85F91B')
    registered = {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}
    if not set(names) <= registered:
        raise ValueError('Missing execution hooks')
    candidates = [r for r in rows if r.get('type') == 'ball_update_execution' and r['step'] - action['trigger'] == 493]
    events = []
    cursor = iter(candidates)
    for name in names:
        event = next((e for e in cursor if e['address'] == name), None)
        if event is None:
            raise ValueError(f'Missing or unordered callback: {name}')
        events.append(event)
    entry, product, corrected, stored, _, initialized, returned = events
    if (entry['angle'], entry['parameter'], entry['magnitude'], entry['global_ac'], entry['global_ae']) != (4, 1, parameter, 0, 0):
        raise ValueError('Unexpected vector inputs or alternate branch')
    components = [int.from_bytes(vector[i:i+2], 'little', signed=True) * parameter for i in (0, 2)]
    words = [(v >> 16 & 0xffff, v & 0xffff) for v in components]
    if words != [(product['scratch_00'], product['scratch_02']), (product['scratch_04'], product['scratch_06'])]:
        raise ValueError('Mode 7 products differ')
    if [(corrected['scratch_00'], corrected['scratch_02']), (corrected['scratch_04'], corrected['scratch_06'])] != words:
        raise ValueError('Unexpected sign correction')
    if [(stored['vx'], stored['vx_fraction']), (stored['vy'], stored['vy_fraction'])] != words:
        raise ValueError('Ball velocity does not match output words')
    if initialized['vz'] != 0 or initialized['vz_fraction'] != 0 or returned['timer'] != 12:
        raise ValueError('Unexpected initialization results')
    return {'schema': 'issd-type1-vector/v1', 'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'sources': [{'path': p.as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace, neutral)],
            'baseline_samples': proof['before_compared'], 'rom_entries': {'parameter_offset': '0xA378',
            'parameter': parameter, 'vector_offset': '0xA5E7', 'vector_hex': vector.hex()},
            'components_signed_32': components, 'velocity_words': words, 'events': events,
            'limitations': ['One angle, magnitude and execution path; other signs and branches need validation.',
                            'Native fixed-point words are not calibrated Canvas velocities.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom', type=Path); p.add_argument('trace', type=Path); p.add_argument('neutral', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = analyze(a.rom.read_bytes(), a.trace, a.neutral)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('Validated type-1 fixed-point velocity against ROM and replay')
