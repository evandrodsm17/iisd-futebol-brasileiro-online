"""Compare captured reaction operands with roster bytes, without assigning identity."""
import argparse
import hashlib
import json
from pathlib import Path

from extract_issd_catalog import EXPECTED_MD5, ROM_ATTR_BASE, PLAYERS_PER_TEAM, ATTR_BYTES, TEAMS


def sha(data):
    return hashlib.sha256(data).hexdigest()


def audit(rom, catalog, jump, fall):
    raw = rom.read_bytes()
    header = len(raw) % 0x8000
    image = raw[header:]
    if header not in (0, 512) or hashlib.md5(image).hexdigest() != EXPECTED_MD5:
        raise ValueError('Unexpected ROM revision')
    catalog_bytes, jump_bytes, fall_bytes = catalog.read_bytes(), jump.read_bytes(), fall.read_bytes()
    teams = json.loads(catalog_bytes)['teams']
    jump_record, fall_record = json.loads(jump_bytes)['record'], json.loads(fall_bytes)['record']
    fields = ('record_word', 'record_next_word', 'record_sixth_word')
    if [jump_record[k] for k in fields] != [fall_record[k] for k in fields]:
        raise ValueError('Replay operands differ')
    candidates = []
    if len(teams) != TEAMS:
        raise ValueError('Unexpected catalog size')
    for team_index, team in enumerate(teams):
        if len(team['players']) != PLAYERS_PER_TEAM:
            raise ValueError('Unexpected roster size')
        for slot, player in enumerate(team['players']):
            offset = ROM_ATTR_BASE + (team_index * PLAYERS_PER_TEAM + slot) * ATTR_BYTES
            attrs = image[offset:offset + ATTR_BYTES]
            if attrs.hex() != player['raw']['attributes_hex'].lower():
                raise ValueError('Catalog and ROM roster bytes differ')
            if int.from_bytes(attrs[2:4], 'little') == jump_record['record_word'] and int.from_bytes(attrs[3:5], 'little') == jump_record['record_next_word']:
                candidates.append({'team_id': team['id'], 'team': team['name'], 'slot': slot,
                                   'player': player['name'], 'attributes_hex': attrs.hex(),
                                   'rom_offset': f'0x{offset:06X}'})
    if len(candidates) != 1:
        raise ValueError('Unexpected candidate count')
    return {'schema': 'issd-reaction-catalog-candidate/v1', 'rom_sha256': sha(image),
            'catalog_sha256': sha(catalog_bytes), 'jump_report_sha256': sha(jump_bytes),
            'fall_report_sha256': sha(fall_bytes), 'record_words': {k: jump_record[k] for k in fields},
            'comparison': 'catalog raw bytes 2..4 against the two overlapping captured words',
            'candidates': candidates,
            'limits': ['Matching three bytes does not prove runtime player identity or that all roster records are copied unchanged.',
                       'The low nibble of the captured word at X+6 is runtime data and is not derived from the seven catalog bytes.',
                       'Attribute labels and scaling must be validated independently; decoded browser ratings are not used.',
                       'The runtime slot mapping, editable data, and global state remain unresolved.',
                       'The ROM remains local.']}


def main():
    parser = argparse.ArgumentParser()
    for name in ('rom', 'catalog', 'jump', 'fall', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    report = audit(args.rom, args.catalog, args.jump, args.fall)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"OK: ROM matches 720 catalog records; {len(report['candidates'])} raw-byte candidate")


if __name__ == '__main__':
    main()
