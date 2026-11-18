"""Validate shot-index calculations against a local automated ROM trace."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    for offset, expected in ((0x61e44, 'e2 20 a2 04 00 ad 0d 14 29 0b dd d8 dd f0 06 ca 10 f3 a2 02 00 c2 20 8a 60'),
                             (0x61f1c, '64 33 20 44 9e 8d 06 17'),
                             (0x61f4f, 'ad aa 14 89 10 00 d0 0f ad 06 17 18 69 05 00 8d 06 17'),
                             (0xddd8, '01 09 08 0a 02')):
        value = bytes.fromhex(expected)
        if rom[offset:offset + len(value)] != value:
            raise ValueError(f'Unexpected ROM bytes at {offset:06x}')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or overridden trace')
    ends = [e for e in driver if e.get('type') == 'session_end']
    config = [e for e in driver if e.get('type') == 'penalty_direction_config']
    if len(ends) != 1 or ends[0]['steps'] != 16000 or ends[0]['reason'] != 'frame_limit' or len(config) != 1 or config[0]['direction'] != 'Right' or config[0]['controllers'] != 'p1':
        raise ValueError('Unexpected run configuration')
    sites = ['penalty_shot_decode_start', 'penalty_shot_decode_end', 'penalty_shot_base_written', 'penalty_shot_final']
    events = [e for e in hooks if e['site'] in sites]
    if not events or len(events) % 4:
        raise ValueError('Incomplete shot-index calculations')
    calculations = []
    for i in range(0, len(events), 4):
        group = events[i:i + 4]
        if [e['site'] for e in group] != sites or len({e['frame'] for e in group}) != 1:
            raise ValueError('Unpaired shot-index calculation')
        start, end, base_written, final = group
        code = (start['input_word'] >> 8) & 0x0b
        table = [1, 9, 8, 10, 2]
        base = table.index(code) if code in table else 2
        index = base + (0 if final['flags'] & 0x10 else 5)
        if end['a'] != base or base_written['direction'] != base or final['direction'] != index:
            raise ValueError('Shot-index calculation mismatch')
        calculations.append({'frame': start['frame'], 'side': start['side'], 'input_word': start['input_word'],
                             'flags': final['flags'], 'code': code, 'base': base, 'index': index})
    writes = [e for e in hooks if e['site'] == 'penalty_history_before']
    linked = []
    for write in writes:
        earlier = [c for c in calculations if c['frame'] <= write['frame'] and c['side'] == write['side'] and c['frame'] >= 0]
        if earlier:
            latest = max(earlier, key=lambda c: c['frame'])
            if latest['index'] == write['source_direction']:
                linked.append({'calculation_frame': latest['frame'], 'write_frame': write['frame'], 'index': latest['index']})
    if len(calculations) != 8 or len(writes) != 8 or len(linked) != 8 or any(e['calculation_frame'] != e['write_frame'] for e in linked):
        raise ValueError('Unexpected shot calculation to history relationship')
    return {'schema': 'issd-penalty-shot-direction/v1', 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(raw).hexdigest(), 'calculations': calculations, 'matching_history_writes': linked,
            'limits': ['One synthetic shootout; input and flag combinations are not exhaustive.',
                       'Indices are not independently mapped to on-screen trajectories.', 'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['calculations']), 'shot-index calculations audited')
