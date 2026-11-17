"""Compare the ROM thresholds and 55 recorded decision-branch observations."""
import argparse
import collections
import hashlib
import json
from pathlib import Path


def decision(home, away, side, round_no):
    if side not in (0, 2) or not 0 <= home <= 127 or not 0 <= away <= 127:
        raise ValueError('Unmodelled native input')
    difference = home - away
    if round_no >= 5:
        return side != 0 and difference != 0
    limits = ([5, 5, 5, 3, 2], [5, 5, 3, 2, 1])
    limit = limits[side // 2][round_no] - (side == 0 and difference < 0)
    return abs(difference) >= limit


def audit(rom_path, hooks_path):
    rom, raw = rom_path.read_bytes(), hooks_path.read_bytes()
    # LoROM $81:DDCE and $81:DDD3, unheadered USA image.
    if rom[0xddce:0xddd8] != bytes([5, 5, 5, 3, 2, 5, 5, 3, 2, 1]):
        raise ValueError('Unexpected ROM threshold tables')
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete hook trace')
    checks = [(i, h) for i, h in enumerate(hooks) if h['site'] == 'penalty_check']
    if len(checks) != 55:
        raise ValueError('Unexpected number of checks')
    branches, phases = 0, collections.Counter()
    for n, (index, check) in enumerate(checks):
        end = checks[n + 1][0] if n + 1 < len(checks) else len(hooks)
        observed = any(h['site'] == 'penalty_winner' and h['frame'] == check['frame'] for h in hooks[index + 1:end])
        expected = decision(check['penalty_home'], check['penalty_away'], check['side'], check['round'])
        if observed != expected:
            raise ValueError(f"Decision mismatch at frame {check['frame']}")
        branches += observed
        phases['first_five' if check['round'] < 5 else 'after_five'] += 1
    return {'schema': 'issd-penalty-decision/v1', 'hook_sha256': hashlib.sha256(raw).hexdigest(),
            'rom_table_offset': '0xddce', 'table_bytes': list(rom[0xddce:0xddd8]),
            'checks': len(checks), 'entered_winner_branch': branches, 'checks_by_phase': dict(phases),
            'limits': ['One synthetic shootout, including hypothetical checks with temporarily incremented counters.',
                       'Round and side are native fields; mapping to user controls is not established.',
                       'Branch entry is not necessarily a final result.', 'ROM and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'hooks', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.hooks)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', result['checks'], 'penalty decisions agree with ROM tables')
