"""Link two observed release paths to the initial native ball type."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, root):
    rom = rom_path.read_bytes()
    checks = {
        0x2f694: '9c ca 17 22 ce e3 80 a5 6e 89 00 08 d0 18',
        0x2f6ba: '22 b0 e7 80 a5 40 4a 90 1a',
        0x2f71f: '9e d4 80 a2 05 00 a4 82 4c 9b f8',
        0x2f871: '9c b4 00 9c d8 19 9c dc 12 9c da 12 9c ae 00 8e 00 00 8e f4 12',
        0x2f89b: '9c b4 00 9c d8 19 8e 00 00 8e f4 12',
        0x194eb: 'a5 00 8d 30 04 8d 76 04',
    }
    for offset, expected in checks.items():
        if not rom[offset:].startswith(bytes.fromhex(expected)):
            raise ValueError(f'Unexpected native instructions at {offset:x}')
    result = {}
    for side, expected_type, expected_path in [('right', 3, '85F871'), ('left', 5, '85F89B')]:
        directory = root / ('shot-charge-' + side)
        trace, = [p for p in directory.glob('issd-auto-probe-*.jsonl') if p.stat().st_size]
        trace_raw = trace.read_bytes()
        samples = [json.loads(line) for line in trace_raw.splitlines()]
        hook_raw = (directory / 'charge-hooks.jsonl').read_bytes()
        hooks = [json.loads(line) for line in hook_raw.splitlines()]
        if not any(e.get('type') == 'session_end' for e in hooks):
            raise ValueError('Incomplete hook trace')
        releases = [e for e in hooks if e.get('site') == expected_path]
        if len(releases) != 1:
            raise ValueError('Unexpected release count')
        release = releases[0]
        branch = [e for e in hooks if e.get('site') == '85F694' and e['frame'] == release['frame'] and e['d'] == release['d']]
        if len(branch) != 1 or release['x'] != expected_type:
            raise ValueError('Unexpected branch or type')
        if bool(branch[0]['flags6e'] & 0x800) != (side == 'left') or (branch[0]['flags6e'] ^ release['flags6e']) & 0x800:
            raise ValueError('Unexpected entry flag')
        if side == 'left' and not any(e.get('site') == '85F70C' and e['frame'] == release['frame'] and e['d'] == release['d'] for e in hooks):
            raise ValueError('Unobserved type-5 path')
        if release['y'] != (11 if side == 'right' else release['charge']):
            raise ValueError('Unexpected release parameter')
        following = [s for s in samples if release['frame'] <= s.get('frame', -1) <= release['frame'] + 5 and s.get('ball', {}).get('type') == expected_type and s.get('link_a6') == 0]
        if not following:
            raise ValueError('No subsequent unowned ball with the selected type')
        first = min(following, key=lambda s: s['frame'])
        result[side] = {'entry_frame': release['frame'], 'entry_flag': branch[0]['flags6e'], 'release_path': expected_path,
                        'selected_type': expected_type, 'parameter': release['y'], 'free_ball_frame': first['frame'],
                        'trace_sha256': hashlib.sha256(trace_raw).hexdigest(), 'hooks_sha256': hashlib.sha256(hook_raw).hexdigest()}
    return {'schema': 'issd-shot-type-selection/v1', 'cases': result,
            'limitations': ['Two captures of one actor and saved state; no universal mapping to web controls.',
                            'The type-6 branch is a static deduction, not observed here.',
                            'The post-helper actor word was not directly recorded; type-5 path establishes its low bit was clear.',
                            'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'root', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    report = audit(args.rom, args.root)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print('OK: two release branches matched subsequent ball types')
