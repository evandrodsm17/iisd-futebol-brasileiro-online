"""Correlate observed collision, contact, deferred resolution and local screenshots."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(rom_path, directory):
    rom = rom_path.read_bytes()
    expected = bytes.fromhex('ad aa 14 89 20 00 d0 16 a9 00 08 0c aa 14 a9 00 01 1c aa 14')
    if rom[0x6150a:0x6150a + len(expected)] != expected:
        raise ValueError('Unexpected contact flag instructions')
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    hooks = [json.loads(line) for line in raw.splitlines()]
    if hooks[0]['site'] != 'session_start' or hooks[-1]['site'] != 'session_end':
        raise ValueError('Incomplete hook trace')
    def events(site): return [e for e in hooks if e['site'] == site]
    contacts = events('penalty_contact_action')
    if len(contacts) != 3:
        raise ValueError('Unexpected contact count')
    cases = []
    for number, contact in enumerate(contacts, 1):
        def same_shot(e): return e['side'] == contact['side'] and e['round'] == contact['round']
        collisions = [e for e in events('penalty_collision_selected') if same_shot(e) and e['frame'] == contact['frame'] - 1 and contact['linked_object'] == e['d']]
        starts = [e for e in events('penalty_deferred_start') if same_shot(e) and 0 < e['frame'] - contact['frame'] <= 4]
        finals = [e for e in events('penalty_deferred_finalize') if same_shot(e) and e['frame'] > contact['frame']]
        if len(collisions) != 1 or len(starts) != 1 or len(finals) != 1:
            raise ValueError('Unmatched contact chain')
        collision, start, final = collisions[0], starts[0], finals[0]
        if collision['linked_object'] != start['d'] or not start['shot_flags'] & 0x0800 or contact['shot_flags'] & 0x0800:
            raise ValueError('Unexpected object link or flag')
        if (contact['penalty_home'], contact['penalty_away']) != (final['penalty_home'], final['penalty_away']):
            raise ValueError('Penalty score changed during deferred contact')
        image = (directory / f'mode-hooks.jsonl-contact-{number}.png').read_bytes()
        if not image.startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('Missing contact image')
        cases.append({'collision': collision, 'contact': contact, 'deferred_start': start, 'deferred_final': final,
                      'contact_image_sha256': hashlib.sha256(image).hexdigest()})
    return {'schema': 'issd-penalty-contact/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(), 'cases': cases,
            'limits': ['Only three contacts from one synthetic shootout were observed.',
                       'Images were visually inspected; identification is not automated.',
                       'The complete mapping of object fields and contact hitboxes is not established.',
                       'ROM, images and raw trace remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['cases']), 'contact chains audited')
