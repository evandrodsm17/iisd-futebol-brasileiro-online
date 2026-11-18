"""Audit natural animation selector writes and collision uses in one isolated run."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    if rom[0x6152d:0x6153c] != bytes.fromhex('88 88 b1 24 29 ff 00 c9 7f 00 b0 02 85 14 60'):
        raise ValueError('Unexpected selector-write instructions')
    if rom[0xdebb:0xdec2] != bytes.fromhex('00 00 1c 00 1e 00 ff'):
        raise ValueError('Unexpected sequence bytes')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    driver_path, = directory.glob('issd-auto-probe-*.jsonl')
    driver_raw = driver_path.read_bytes()
    driver = [json.loads(line) for line in driver_raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end' or any(e['site'] in ('error', 'synthetic_selector_config') for e in hooks):
        raise ValueError('Incomplete or forced-selector trace')
    ends = [e for e in driver if e.get('type') == 'session_end']
    configs = [e for e in driver if e.get('type') == 'competition_config']
    if len(ends) != 1 or ends[0]['steps'] != 10800 or ends[0]['reason'] != 'frame_limit' or len(configs) != 1 or configs[0]['menu_mode'] != 'world_series' or not configs[0]['synthetic_fast_clock_and_score']:
        raise ValueError('Unexpected route or duration')
    writes = [e for e in hooks if e['site'] == 'penalty_selector_write']
    if not writes:
        raise ValueError('No selector writes')
    direct = [e for e in writes if not e['indexed_load']]
    if not direct or any(e['source'] != -1 or e['source_byte'] != -1 for e in direct):
        raise ValueError('Direct and indexed selector paths were not distinguished')
    selected = [e for e in writes if e['value'] == 30]
    checks = [e for e in hooks if e['site'] in ('collision_hit', 'collision_miss') and e['selector'] == 30]
    if len(selected) != 2 or len(checks) != 8 or any(e['site'] != 'collision_miss' for e in checks):
        raise ValueError('Unexpected natural selector observations')
    cases = []
    for event in selected:
        if (not event['indexed_load'] or event['old'] != 28 or event['source'] != 0xdebf or event['animation_state'] != 0x9196 or
                event['bank'] != 0x81 or event['source'] != (event['index'] + event['sequence_offset']) & 0xffff or
                event['source_byte'] != 30 or rom[event['source']] != 30):
            raise ValueError('Unexpected selector source or animation state')
        next_writes = [e for e in writes if e['d'] == event['d'] and e['frame'] > event['frame']]
        if not next_writes:
            raise ValueError('Missing next animation state')
        next_write = min(next_writes, key=lambda e: e['frame'])
        if next_write['old'] != 30 or next_write['value'] != 14:
            raise ValueError('Unexpected next selector')
        associated = [e for e in checks if e['dp'] == event['d'] and event['frame'] <= e['frame'] < next_write['frame']]
        if len(associated) != 4 or any(e['table_pointer'] != 0xde85 or e['original_selector'] != -1 for e in associated):
            raise ValueError('Unexpected associated collision checks')
        image = (directory / f"mode-hooks.jsonl-selector-30-{event['d']}.png").read_bytes()
        if not image.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Missing selector image')
        cases.append({'selector_write': event, 'next_selector_write': next_write,
                      'collision_checks': associated, 'image_sha256': hashlib.sha256(image).hexdigest()})
    return {'schema': 'issd-penalty-pose-selector/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'driver_sha256': hashlib.sha256(driver_raw).hexdigest(), 'total_selector_changes': len(writes), 'cases': cases,
            'limits': ['Score, clock and menu commands were synthetic; selector was not overridden.',
                       'Some callers enter after the indexed load, so the logged source fields do not apply to every write.',
                       'Only two uses of selector 0x1e and their sampled collision checks were analyzed.',
                       'Images were visually reviewed; sprite pose and directions are not automatically classified.',
                       'ROM, raw traces and images remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'natural selector uses and associated collision checks')
