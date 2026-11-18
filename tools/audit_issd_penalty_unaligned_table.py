"""Audit a synthetic selector override and the native unaligned final read."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    if rom[0xde85:0xde8f] != bytes.fromhex('8e de 04 de 04 f8 e2 05 f8 00'):
        raise ValueError('Unexpected table or adjacent byte')
    if rom[0x623b1:0x623b4] != bytes.fromhex('f9 03 00'):
        raise ValueError('Unexpected indexed subtract instruction')
    hook_raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in hook_raw.splitlines()]
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete hook trace')
    if any(e['site'] == 'error' for e in hooks):
        raise ValueError('Probe reported an error')
    config = [e for e in hooks if e['site'] == 'synthetic_selector_config']
    summary = [e for e in hooks if e['site'] == 'synthetic_selector_summary']
    ending = [e for e in driver if e.get('type') == 'session_end']
    competition = [e for e in driver if e.get('type') == 'competition_config']
    if len(competition) != 1 or competition[0]['menu_mode'] != 'world_series' or not competition[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Unexpected competition configuration')
    if len(config) != 1 or config[0]['value'] != 30 or len(summary) != 1 or summary[0]['writes'] == 0 or summary[0]['writes'] != summary[0]['restores']:
        raise ValueError('Unexpected override or restore count')
    if len(ending) != 1 or ending[0]['steps'] != 10800 or ending[0]['reason'] != 'frame_limit':
        raise ValueError('Incomplete driver trace')
    reads = []
    for i, before in enumerate(hooks):
        if before['site'] != 'selector_last_upper_normal':
            continue
        after = hooks[i + 1] if i + 1 < len(hooks) else {}
        if after.get('site') != 'selector_last_after_upper_normal' or after['frame'] != before['frame']:
            raise ValueError('Unpaired indexed read')
        if before['y'] != 0xde8b or before['b'] != 0x81 or before['bus_81'] != 0 or before['bus_00'] != 0x65 or before['a'] != after['a']:
            raise ValueError('Unexpected bank, adjacent byte or arithmetic')
        reads.append({'frame': before['frame'], 'bank': before['b'], 'y': before['y'],
                      'address': '81:DE8E', 'byte': before['bus_81'], 'a_before': before['a'], 'a_after': after['a']})
    if not reads:
        raise ValueError('No observed read beyond the declared end')
    return {'schema': 'issd-penalty-unaligned-table/v1', 'hook_sha256': hashlib.sha256(hook_raw).hexdigest(),
            'driver_sha256': hashlib.sha256(driver_raw).hexdigest(), 'selector_override': 30,
            'override_summary': summary[0], 'records': [[4, 222, 4, 248], [226, 5, 248, 0]], 'reads': reads,
            'limits': ['The selector, score and clock were modified synthetically in an isolated run.',
                       'Only the normal indexed upper comparison was observed reading the adjacent byte.',
                       'Natural selection and animation semantics of selector 0x1e are not established.',
                       'ROM and raw traces stay local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['reads']), 'adjacent-byte reads and selector restores audited')
