"""Compare same-frame native coordinates to ROM offsets; never infer ownership."""
import argparse
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

STATES = (0xB8, 0xC0, 0xC8, 0xD0, 0xD8, 0xE0, 0xE8)


def signed16(value):
    return ((value + 0x8000) & 0xFFFF) - 0x8000


def rom_tables(rom):
    header = len(rom) % 0x8000
    if header not in (0, 512):
        raise ValueError('Unsupported ROM header')
    def read(offset, size):
        data = rom[header+offset:header+offset+size]
        if len(data) != size: raise ValueError('Truncated ROM')
        return data
    fixed = read(0x97C2, 32)
    fixed_pairs = [(signed16(int.from_bytes(fixed[i:i+2], 'little')),
                    signed16(int.from_bytes(fixed[i+2:i+4], 'little')))
                   for i in range(0, 32, 4)]
    # The 8 direction bytes span DATA_819623 and the start of DATA_819629.
    selectors, cycle = read(0x9623, 8), read(0x9842, 64)
    phase_pairs = []
    for selector in selectors:
        pairs = []
        for phase in range(8):
            index = (selector & 0x1F) + phase
            x, y = cycle[index], cycle[32+index]
            x = x if x < 128 else x-256
            y = y if y < 128 else y-256
            pairs.append((-x if selector & 0x80 else x,
                          -y if selector & 0x40 else y))
        phase_pairs.append(pairs)
    raw_turn = read(0x9802, 64)
    turn_pairs = set()
    for i in range(0,64,4):
        x=signed16(int.from_bytes(raw_turn[i:i+2],'little'))
        y=signed16(int.from_bytes(raw_turn[i+2:i+4],'little'))
        turn_pairs.update(((x,y),(-x,-y)))
    return fixed_pairs, phase_pairs, turn_pairs


def analyze(rows, fixed, cycle, turn=()):
    counts = defaultdict(Counter)
    offsets = defaultdict(Counter)
    transitions = Counter()
    previous, last_frame = {}, None
    frames = 0
    for row in rows:
        if row.get('type') == 'session_start': continue
        frame = row['frame']
        if last_frame is not None and frame <= last_frame:
            raise ValueError('Non-monotonic frames')
        contiguous = last_frame is not None and frame == last_frame+1
        globals_ = row['globals']
        ball_x, ball_y = globals_['0408'], globals_['040C']
        current = {}
        for actor in row['actors']:
            words, address = actor['words'], actor['address']
            state, direction = words['0032'], words['002E']
            current[address] = (state, direction)
            if contiguous and address in previous and previous[address][0] != state:
                if state in STATES or previous[address][0] in STATES:
                    transitions[(previous[address][0], state)] += 1
            if state not in STATES: continue
            key = f'{state:04X}'
            counts[key]['samples'] += 1
            if direction not in range(8):
                counts[key]['invalid_direction'] += 1
                continue
            delta = (signed16(ball_x-words['0008']), signed16(ball_y-words['000C']))
            offsets[(key, direction)][delta] += 1
            counts[key]['fixed_pair_matches'] += int(delta == fixed[direction])
            counts[key]['any_cycle_phase_matches'] += int(delta in cycle[direction])
            counts[key]['any_turn_phase_matches'] += int(delta in turn)
            stable = contiguous and previous.get(address) == (state, direction)
            group = 'stable' if stable else 'entry_or_direction_change_or_gap'
            counts[key][group+'_samples'] += 1
            counts[key][group+'_cycle_matches'] += int(delta in cycle[direction])
            counts[key][group+'_turn_matches'] += int(delta in turn)
        previous, last_frame = current, frame
        frames += 1
    return {'schema': 'issd-ball-attachment-observations/v1', 'frames': frames,
            'by_state': dict(sorted(counts.items())),
            'offsets_by_state_direction': [
                {'state': key, 'direction': direction,
                 'top_offsets': [{'dx': delta[0], 'dy': delta[1], 'samples': n}
                                 for delta, n in values.most_common(8)]}
                for (key, direction), values in sorted(offsets.items())],
            'state_transitions': [{'from': f'{a:04X}', 'to': f'{b:04X}', 'count': n}
                                  for (a,b),n in transitions.most_common()],
            'limitations': ['All actor slots are examined; no possession inferred.',
                           'Cycle comparison tests membership in eight phases, not phase order or timing.',
                           'Turn comparison tests membership in all 32 signed phases, not a direction-specific sequence.',
                           'Frame-end samples may follow later writes by other handlers.',
                           'Capture lacks $00A6, ball type and local phase/timers; no release attribution.',
                           'No conversion to Canvas units or physics calibration.']}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path); p.add_argument('rom', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    rom = args.rom.read_bytes()
    digest = hashlib.sha256()
    def rows():
        with args.trace.open('rb') as stream:
            for line in stream:
                digest.update(line)
                if line.strip(): yield json.loads(line)
    result = analyze(rows(), *rom_tables(rom))
    result['source'] = {'trace': args.trace.as_posix(), 'trace_sha256': digest.hexdigest(),
                        'rom_sha256': hashlib.sha256(rom).hexdigest()}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'frames':result['frames'],'by_state':result['by_state']},indent=2))
