"""Compare synthetic mixed-sign vectors with the original CPU and ROM."""
import argparse
import hashlib
import json
from pathlib import Path
from compare_issd_action_trials import compare, load


def analyze_case(rom, header, trace, neutral, wanted):
    action = load(trace)
    proof = compare(action, load(neutral), 0x40)
    if not all(proof[k] for k in ('baseline_matches_observed_fields', 'extended_fields_compared',
                                  'p2_action_input_confirmed', 'p2_control_neutral_in_action_window')):
        raise ValueError('Replay comparison failed')
    rows = [json.loads(line) for line in trace.read_bytes().splitlines() if line.strip()]
    if not any(r.get('type') == 'session_end' and r.get('reason') == 'experiment_window_complete' for r in rows):
        raise ValueError('Incomplete replay')
    overrides = [r for r in rows if r.get('type') == 'synthetic_vector_override']
    if len(overrides) != 1 or (overrides[0]['step']-action['trigger'], overrides[0]['original_a'], overrides[0]['forced_a']) != (493,4,wanted):
        raise ValueError('Unexpected synthetic override')
    names = ('839E32', '839E92', '839EC3', '83953F')
    if not set(names) <= {r['address'] for r in rows if r.get('type') == 'ball_update_hook_registration' and r.get('success')}:
        raise ValueError('Missing hooks')
    cursor = iter(r for r in rows if r.get('type') == 'ball_update_execution' and r['step']-action['trigger'] == 493)
    events = []
    for name in names:
        event = next((e for e in cursor if e['address'] == name), None)
        if event is None:
            raise ValueError(f'Missing {name}')
        events.append(event)
    entry, product, corrected, stored = events
    if entry['a'] != wanted or entry['angle'] != 4 or entry['magnitude'] != 40 or entry['global_ac'] or entry['global_ae']:
        raise ValueError('Unexpected inputs')
    offset = 0xa5d7 + (wanted & 31) * 4
    raw = rom[header+offset:header+offset+4]
    coefficients = [int.from_bytes(raw[i:i+2], 'little', signed=True) for i in (0,2)]
    if coefficients != [615,1522]:
        raise ValueError('Unexpected ROM coefficients')
    unsigned = [v*40 for v in coefficients]
    signed = [unsigned[0] * (-1 if ((wanted+16)&63)>=32 else 1), unsigned[1] * (-1 if wanted>=32 else 1)]
    words = [(v >> 16 & 0xffff, v & 0xffff) for v in signed]
    if [(product['scratch_00'],product['scratch_02']),(product['scratch_04'],product['scratch_06'])] != [(v>>16 & 0xffff,v & 0xffff) for v in unsigned]:
        raise ValueError('Products differ')
    if [(corrected['scratch_00'],corrected['scratch_02']),(corrected['scratch_04'],corrected['scratch_06'])] != words:
        raise ValueError('Sign correction differs')
    if [(stored['vx'],stored['vx_fraction']),(stored['vy'],stored['vy_fraction'])] != words:
        raise ValueError('Stored velocity differs')
    return {'trace':trace.as_posix(),'trace_sha256':hashlib.sha256(trace.read_bytes()).hexdigest(),
            'baseline_samples':proof['before_compared'],'synthetic_override':overrides[0],
            'rom_table_offset':f'0x{offset:X}','coefficients':coefficients,'components_signed_32':signed,
            'velocity_words':words,'events':events}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path);p.add_argument('angle20',type=Path);p.add_argument('angle52',type=Path)
    p.add_argument('neutral',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    rom=a.rom.read_bytes();header=len(rom)%0x8000
    if header not in (0,512):raise ValueError('Unsupported ROM header')
    result={'schema':'issd-type1-mixed-sign-vectors/v1','rom_sha256':hashlib.sha256(rom).hexdigest(),
            'neutral':a.neutral.as_posix(),'neutral_sha256':hashlib.sha256(a.neutral.read_bytes()).hexdigest(),
            'cases':[analyze_case(rom,header,a.angle20,a.neutral,20),analyze_case(rom,header,a.angle52,a.neutral,52)],
            'limitations':['Both angles are synthetic; the ball angle field retains its original value.',
                           'Two points do not prove all angles or the browser coordinate scale.']}
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Validated two synthetic mixed-sign vectors')


if __name__ == '__main__':main()
