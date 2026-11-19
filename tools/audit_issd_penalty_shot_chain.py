"""Connect input, native shot vector and observed resolution in one trace."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path, trace_path):
    rom = rom_path.read_bytes()
    if len(rom) % 0x8000 or hashlib.md5(rom).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected unheadered ROM')
    if rom[0x63d7c:0x63d7f] != bytes([0x28, 0, 0x50]) or rom[0xddd8:0xdddd] != bytes([1, 9, 8, 10, 2]):
        raise ValueError('Unexpected input or vector tables')
    raw = trace_path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    if events[0].get('site') != 'session_start' or events[-1].get('site') != 'session_end':
        raise ValueError('Incomplete trace')
    vectors = [(i, e) for i, e in enumerate(events) if e.get('site') == 'penalty_shot_vector']
    if len(vectors) != 8:
        raise ValueError('Unexpected vector count')
    shots = []
    for n, (index, vector) in enumerate(vectors):
        end = vectors[n + 1][0] if n + 1 < len(vectors) else len(events)
        same = [e for e in events[:index] if e.get('frame') == vector['frame'] and e.get('d') == vector['d']]
        starts = [e for e in same if e.get('site') == 'penalty_shot_decode_start']
        finals = [e for e in same if e.get('site') == 'penalty_shot_final']
        if len(starts) != 1 or len(finals) != 1:
            raise ValueError('Missing shot input')
        start, final = starts[0], finals[0]
        if any(start[k] != vector[k] or final[k] != vector[k] for k in ('side', 'round', 'flags')) or final['direction'] != vector['index']:
            raise ValueError('Shot context mismatch')
        code = (start['input_word'] >> 8) & 0x0b
        table = list(rom[0xddd8:0xdddd])
        base = table.index(code) if code in table else 2
        offset = rom[0x63d7c + vector['variant']] + 2 * base
        if vector['x'] != offset or vector['index'] != base + (0 if vector['flags'] & 0x10 else 5):
            raise ValueError('Input index or table offset mismatch')
        def signed(address):
            return int.from_bytes(rom[address:address+2], 'little', signed=True)
        expected = [signed(0x63d95 + offset), signed(0x63d8b + offset),
                    signed((0x63da9 if vector['flags'] & 0x10 else 0x63d9f) + offset)]
        actual = [vector[k] if vector[k] < 0x8000 else vector[k] - 0x10000 for k in ('dx', 'dy', 'dz')]
        if actual != expected:
            raise ValueError('Vector differs from ROM')
        segment = events[index + 1:end]
        resolved = [e for e in segment if e.get('site') == 'penalty_crossing_resolved' and e.get('side') == vector['side'] and e.get('round') == vector['round'] and e.get('d') == vector['d']]
        if len(resolved) != 1:
            raise ValueError('Missing unique crossing')
        crossing = resolved[0]
        within = [e for e in segment if e.get('frame', -1) <= crossing['frame']]
        goals = [e for e in within if e.get('site') == 'penalty_goal_branch' and e.get('frame') == crossing['frame'] and e.get('d') == vector['d']]
        deferred = [e for e in within if e.get('site') == 'penalty_deferred_finalize' and e.get('frame') == crossing['frame'] and e.get('d') == vector['d']]
        if len(goals) + len(deferred) != 1:
            raise ValueError('Unexpected outcome route')
        shots.append({'frame': vector['frame'], 'resolved_frame': crossing['frame'], 'side': vector['side'], 'round': vector['round'],
                      'input_word': start['input_word'], 'code': code, 'base': base, 'index': vector['index'],
                      'flags': vector['flags'], 'variant': vector['variant'], 'table_offset': offset, 'vector': actual,
                      'resolution': 'goal_branch' if goals else 'deferred',
                      'final_native_position': [crossing['x_coord'], crossing['y_coord'], crossing['height']],
                      'score': [crossing['penalty_home'], crossing['penalty_away']]})
    if sum(shot['resolution'] == 'goal_branch' for shot in shots) != 6:
        raise ValueError('Unexpected observed outcomes')
    return {'schema': 'issd-penalty-shot-chain/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(), 'shots': shots,
            'limits': ['One synthetic shootout with automatic commands and accelerated game clock.',
                       'Native input words are not yet mapped universally to controller roles or visual directions.',
                       'Final native position is the captured resolution position, not proof of uninterrupted flight.',
                       'The two deferred outcomes are not a complete model of keeper contacts or rebounds.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'trace', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.trace)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: {len(result['shots'])} input-to-vector-to-resolution chains")
