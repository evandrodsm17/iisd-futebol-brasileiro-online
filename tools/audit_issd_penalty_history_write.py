"""Audit native penalty history writes, cursor advance and observed later lookup."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    expected = bytes.fromhex('ae 40 14 bd 58 17 18 7f a5 be 8c aa ad 06 17 9f 00 00 81 ae 40 14 bd 58 17 1a 1a 29 1f 00 9d 58 17 60')
    if rom[0x62227:0x62227 + len(expected)] != expected:
        raise ValueError('Unexpected native history-write routine')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or overridden trace')
    end = [e for e in driver if e.get('type') == 'session_end']
    config = [e for e in driver if e.get('type') == 'penalty_direction_config']
    if len(end) != 1 or end[0]['steps'] != 16000 or end[0]['reason'] != 'frame_limit' or len(config) != 1 or config[0]['direction'] != 'Right' or config[0]['controllers'] != 'p1':
        raise ValueError('Unexpected run configuration')
    events = [e for e in hooks if e['site'] in ('penalty_history_before', 'penalty_history_after', 'penalty_history_counter')]
    if len(events) != 24:
        raise ValueError('Unexpected history event count')
    writes = []
    for before, after, counter in zip(events[::3], events[1::3], events[2::3]):
        if [e['site'] for e in (before, after, counter)] != ['penalty_history_before', 'penalty_history_after', 'penalty_history_counter'] or len({e['frame'] for e in (before, after, counter)}) != 1:
            raise ValueError('Unpaired history write')
        side, cursor = before['side'], before['cursor']
        if side not in (0, 2) or cursor not in range(0, 32, 2):
            raise ValueError('Unexpected history cursor')
        offset = (0x1760 if side == 0 else 0x1780) + cursor
        if before['x'] != offset or after['x'] != offset or before['a'] != before['source_direction'] or after['entry'] != before['source_direction'] or counter['cursor'] != ((cursor + 2) & 31):
            raise ValueError('History write mismatch')
        writes.append({'before': before, 'after': after, 'counter': counter})
    reads = [e for e in hooks if e['site'] == 'penalty_cpu_history']
    linked = []
    for read in reads:
        previous = [w for w in writes if w['after']['x'] == read['x'] and w['after']['frame'] < read['frame']]
        if previous:
            latest = max(previous, key=lambda w: w['after']['frame'])
            if latest['after']['entry'] != read['a']:
                raise ValueError('History read differs from last observed write')
            linked.append({'write_frame': latest['after']['frame'], 'read_frame': read['frame'], 'offset': read['x'], 'value': read['a']})
    if len(linked) != 1 or linked[0]['write_frame'] != 10252 or linked[0]['read_frame'] != 10253:
        raise ValueError('Unexpected observed history linkage')
    return {'schema': 'issd-penalty-history-write/v1', 'driver_sha256': hashlib.sha256(driver_raw).hexdigest(),
            'hooks_sha256': hashlib.sha256(raw).hexdigest(), 'writes': writes, 'linked_reads': linked,
            'limits': ['Eight writes from one synthetic shootout; cursor wrap was not observed.',
                       'The semantic meaning of source direction is not independently established.',
                       'One read matched an immediately preceding write; not all CPU choices use history this way.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['writes']), 'history writes and', len(result['linked_reads']), 'linked read audited')
