"""Validate a deliberately overridden angle against the ROM's Mode 7 path."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load


def analyze(rom, trace, neutral):
    header = len(rom) % 0x8000
    if header not in (0, 512) or rom[header+0xa5e7:header+0xa5eb] != bytes.fromhex('280ece05'):
        raise ValueError('ROM vector differs')
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay comparison failed')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    overrides = [r for r in rows if r.get('type') == 'synthetic_vector_override']
    if len(overrides) != 1 or (overrides[0]['step']-action['trigger'], overrides[0]['original_a'], overrides[0]['forced_a']) != (493, 4, 36):
        raise ValueError('Missing or unexpected synthetic override')
    names = ('839E32', '839E92', '839EC3', '83953F')
    registered = {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}
    if not set(names) <= registered:
        raise ValueError('Missing hooks')
    cursor = iter(r for r in rows if r.get('type') == 'ball_update_execution' and r['step']-action['trigger'] == 493)
    events = []
    for name in names:
        event = next((e for e in cursor if e['address'] == name), None)
        if event is None:
            raise ValueError(f'Missing event {name}')
        events.append(event)
    entry, product, corrected, stored = events
    if entry['a'] != 36 or entry['angle'] != 4 or entry['magnitude'] != 40 or entry['global_ac'] or entry['global_ae']:
        raise ValueError('Unexpected synthetic inputs')
    components = [-3624*40, -1486*40]
    words = [(v >> 16 & 0xffff, v & 0xffff) for v in components]
    if [(product['scratch_00'], product['scratch_02']), (product['scratch_04'], product['scratch_06'])] != [(2, 13888), (0, 59440)]:
        raise ValueError('Unexpected unsigned products')
    if [(corrected['scratch_00'], corrected['scratch_02']), (corrected['scratch_04'], corrected['scratch_06'])] != words:
        raise ValueError('Unexpected sign correction')
    if [(stored['vx'], stored['vx_fraction']), (stored['vy'], stored['vy_fraction'])] != words:
        raise ValueError('Stored vector differs')
    return {'schema':'issd-type1-opposite-vector/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'sources':[{'path':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (trace,neutral)],
            'baseline_samples':proof['before_compared'], 'synthetic_override':overrides[0],
            'components_signed_32':components, 'velocity_words':words, 'events':events,
            'limitations':['Angle was forced at routine entry; the recorded ball angle remains 4.',
                           'One synthetic case cannot prove all directions or browser scaling.']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('trace',type=Path);p.add_argument('neutral',type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=analyze(a.rom.read_bytes(),a.trace,a.neutral)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Validated synthetic opposite vector and sign correction')
