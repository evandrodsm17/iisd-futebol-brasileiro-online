"""Correlate observed crossing, deferred resolution, and penalty decision hooks."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_issd_catalog import EXPECTED_MD5


def audit(rom_path, trace_path):
    rom = rom_path.read_bytes()
    if len(rom) % 0x8000 or hashlib.md5(rom).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected unheadered ROM')
    # LoROM: crossing sets flags and calls $8C9CE5, which reaches $8C9D18.
    expected = {0x60dc1: bytes.fromhex('09 41 00 8d aa 14 22 e5 9c 8c'),
                0x61ce5: bytes.fromhex('ad aa 14 89 20 00 d0 2b ad aa 14 89 00 20 d0 23'),
                0x61d83: bytes.fromhex('af 42 d4 7e 48 22 18 9d 8c'),
                0x61e25: bytes.fromhex('68 8f 42 d4 7e 6b')}
    for offset, sequence in expected.items():
        if rom[offset:offset + len(sequence)] != sequence:
            raise ValueError(f'Unexpected ROM bytes at {offset:x}')
    raw = trace_path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    if events[0].get('site') != 'session_start' or events[-1].get('site') != 'session_end':
        raise ValueError('Incomplete trace')
    crossings = [(i, event) for i, event in enumerate(events) if event.get('site') == 'penalty_crossing_resolved']
    if len(crossings) != 20:
        raise ValueError('Unexpected number of crossing events')
    results = []
    for index, crossing in crossings:
        frame = crossing['frame']
        same = [event for event in events[index + 1:] if event.get('frame') == frame]
        checks = [event for event in same if event.get('site') == 'penalty_check']
        if len(checks) != 1:
            raise ValueError(f'Unexpected same-frame decision at {frame}')
        check = checks[0]
        keys = ('d', 'side', 'round', 'penalty_home', 'penalty_away')
        if any(crossing[k] != check[k] for k in keys):
            raise ValueError(f'Decision context mismatch at {frame}')
        prior = [event for event in events[:index] if event.get('frame') == frame]
        goal = [event for event in prior if event.get('site') == 'penalty_goal_branch']
        increments = [event for event in prior if event.get('site') == 'penalty_increment']
        deferred = [event for event in prior if event.get('site') == 'penalty_deferred_finalize']
        if len(goal) != len(increments) or len(goal) > 1 or len(deferred) > 1:
            raise ValueError(f'Unexpected earlier hooks at {frame}')
        if deferred:
            starts = [event for event in events[:index] if event.get('site') == 'penalty_deferred_start'
                      and event['side'] == crossing['side'] and event['round'] == crossing['round'] and event['d'] == crossing['d']]
            if len(starts) != 1 or starts[0]['frame'] >= frame:
                raise ValueError(f'Unpaired deferred state at {frame}')
        results.append({'frame': frame, 'side': crossing['side'], 'round': crossing['round'],
                        'score': [crossing['penalty_home'], crossing['penalty_away']],
                        'goal_branch': bool(goal), 'deferred_finalize': bool(deferred),
                        'winner_branch': any(event.get('site') == 'penalty_winner' for event in same)})
    if sum(x['goal_branch'] for x in results) != 15 or sum(x['deferred_finalize'] for x in results) != 3 or sum(x['winner_branch'] for x in results) != 1:
        raise ValueError('Unexpected captured summary')
    return {'schema': 'issd-penalty-resolution-path/v1', 'trace_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_offsets_checked': [hex(x) for x in expected], 'results': results,
            'limits': ['One synthetic replay with automatic inputs and accelerated game clock.',
                       'Same-frame order and matching context are evidence for this trace, not all possible branches or kicks.',
                       'Crossing may be reached after deferred handling; its native coordinates are not mapped to the web field.',
                       'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for arg in ('rom', 'trace', 'output'):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.trace)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: {len(result['results'])} crossing-to-decision paths; 3 after deferred handling")
