"""Audit field-side flag and release path in controlled saved-state replays."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, trace_path):
    rom = rom_path.read_bytes()
    checks = {0x6770: 'a9 00 08 14 6e a5 6e 4a a5 2a b0 07 cd f2 12 10 07 18 6b cd f2 12 10 f9 a9 00 08 04 6e 38 6b',
              0x2f6be: 'a5 40 4a 90 1a'}
    for offset, expected in checks.items():
        if not rom[offset:].startswith(bytes.fromhex(expected)):
            raise ValueError(f'Unexpected ROM bytes at {offset:x}')
    raw = trace_path.read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    if events[0]['type'] != 'session_start' or events[-1]['type'] != 'session_end':
        raise ValueError('Incomplete trace')
    cases = []
    for trial, duration in enumerate((1, 3, 6, 10, 15, 20), 1):
        rows = [e for e in events if e.get('trial') == trial]
        config = [e for e in rows if e['type'] == 'case']
        if len(config) != 1 or config[0]['heldFrames'] != duration:
            raise ValueError('Unexpected input case')
        def hook(name):
            found = [e for e in rows if e['type'] == 'hook' and e['site'] == name]
            if len(found) != 1:
                raise ValueError(f'Expected one {name} hook in trial {trial}')
            return found[0]
        entry, selected, release_entry, post_helper, release = [hook(s) for s in ('80E770','80E788','85F694','85F6BE','85F89B')]
        diff = (entry['actor2a'] - entry['middle']) & 0xffff
        set_flag = bool(diff & 0x8000) if entry['flags'] & 1 else not bool(diff & 0x8000)
        if not set_flag or selected['step'] != entry['step'] or not (release_entry['flags'] & 0x800) or post_helper['actor40'] & 1:
            raise ValueError('Unexpected selector branch')
        if release['x'] != 5 or release['y'] != release['charge'] or release['step'] != post_helper['step']:
            raise ValueError('Unexpected release parameters')
        frames = [e for e in rows if e['type'] == 'frame' and e['step'] >= release['step'] and e['carrier'] == 0 and e['ballType'] == 5]
        if not frames:
            raise ValueError('No corresponding free ball')
        cases.append({'held_frames':duration, 'flags_before':entry['flags'], 'actor_coordinate':entry['actor2a'],
                      'boundary':entry['middle'], 'branch_set':set_flag, 'release_flags':release_entry['flags'],
                      'post_helper_word':post_helper['actor40'], 'charge':release['charge'], 'ball_type':release['x'],
                      'release_step':release['step'], 'free_ball_step':min(e['step'] for e in frames)})
    return {'schema':'issd-shot-release-detail/v1', 'trace_sha256':hashlib.sha256(raw).hexdigest(), 'cases':cases,
            'limitations':['One pre-shot state and actor; six durations do not establish other field positions or input mappings.',
                           'The unset branch, helper odd output and type-6 release were not observed.',
                           'ROM, savestate and raw trace remain local.']}


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    for name in ('rom','trace','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args()
    result=audit(args.rom,args.trace)
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print('OK:',len(result['cases']),'field checks and shot releases verified')
