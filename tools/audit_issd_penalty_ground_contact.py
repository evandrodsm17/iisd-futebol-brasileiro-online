"""Correlate penalty ground-contact and stop branch executions with movement."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_issd_penalty_shot_vector import audit as audit_vectors


def signed(word):
    return word if word < 0x8000 else word - 0x10000


def audit(rom_path, directory):
    vectors = audit_vectors(rom_path, directory)
    raw = (directory / 'mode-hooks.jsonl').read_bytes()
    events = [json.loads(line) for line in raw.splitlines()]
    contacts = [e for e in events if e['site'] == 'penalty_ground_contact']
    stops = [e for e in events if e['site'] == 'penalty_vertical_stop']
    def match(sample, candidates):
        found = [e for e in candidates if all(e[k] == sample[k] for k in ('frame', 'd', 'side', 'round'))]
        if len(found) != 1:
            raise ValueError('Expected one branch execution on the movement frame')
        return found[0]
    linked_contacts = []
    for s in vectors['bounce_pattern']:
        e = match(s, contacts)
        if (signed(e['height']) <= 0 or e['position_low'] != (s['position'] + s['velocity']) % 65536
                or e['gravity'] != 32 or e['velocity'] != (s['velocity'] + e['gravity']) % 65536):
            raise ValueError('Contact state differs from expected ground branch')
        linked_contacts.append({'frame': e['frame'], 'height': signed(e['height']), 'velocity_after_gravity': signed(e['velocity'])})
    linked_stops = []
    for s in vectors['stop_pattern']:
        e = match(s, stops)
        if abs(signed(e['height'])) >= 2 or abs(signed(e['velocity'])) >= 0x40:
            raise ValueError('Stop branch threshold mismatch')
        linked_stops.append({'frame': e['frame'], 'height': signed(e['height']), 'velocity': signed(e['velocity'])})
    if len(linked_contacts) != 19 or len(linked_stops) != 7:
        raise ValueError('Unexpected capture coverage')
    return {'schema': 'issd-penalty-ground-contact/v1', 'hooks_sha256': hashlib.sha256(raw).hexdigest(),
            'driver_sha256': vectors['driver_sha256'], 'linked_contacts': linked_contacts, 'linked_stops': linked_stops,
            'limits': ['One synthetic shootout, not exhaustive physics validation.',
                       'These observations concern the penalty scene; regular gameplay may use a different routine.',
                       'ROM and raw traces remain local.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('rom', 'directory', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.directory)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print('OK:', len(result['linked_contacts']), 'ground contacts and', len(result['linked_stops']), 'stops linked')
