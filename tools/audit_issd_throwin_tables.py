"""Inspect the throw-in pose pointer tables in the supported local ISSD ROM."""
import argparse
import hashlib
import json
from pathlib import Path

from render_issd_descriptor_sprite import span

EXPECTED = 'd2fe66c1ce66c65ce14e478c94be2e616f9e2cad374b5783a6a64d3c1a99cfa9'


def words(rom, address, count):
    raw = span(rom, address, count * 2)
    return [raw[i] | raw[i + 1] << 8 for i in range(0, len(raw), 2)]


def inspect(rom):
    digest = hashlib.sha256(rom).hexdigest()
    if digest != EXPECTED:
        raise ValueError('Unexpected ROM revision')
    hold_pointers = words(rom, 0x82D606, 8)
    transition = words(rom, 0x82D65E, 8)
    release_pointers = words(rom, 0x82D66E, 8)
    directions = []
    for index, (hold, middle, release) in enumerate(zip(hold_pointers, transition, release_pointers)):
        directions.append({'direction_index': index, 'hold_table': hold,
                           'hold_descriptors_raw': words(rom, 0x820000 | hold, 8),
                           'transition_descriptor': middle, 'release_table': release,
                           'release_descriptors': words(rom, 0x820000 | release, 3)})
    return {'schema': 'issd-throwin-rom-tables/v1', 'rom_sha256': digest,
            'hold_table': '82:D606', 'hold_timing_bytes': list(span(rom, 0x82D616, 8)),
            'transition_table': '82:D65E', 'release_table': '82:D66E',
            'release_timing_bytes': list(span(rom, 0x82D67E, 4)),
            'directions': directions,
            'limitations': ['Direction indices are not mapped to browser controls.',
                            'Raw high-bit flags and timing bytes are not interpreted here.',
                            'Tables alone do not prove rendered OAM, per-team appearance, or complete timing.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = inspect(args.rom.read_bytes())
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('Read', len(report['directions']), 'direction entries from the verified ROM')
