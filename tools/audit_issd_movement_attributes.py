"""Verify the static path from roster byte zero to per-actor fields."""
import argparse
import hashlib
import json
from pathlib import Path


def transform(raw, state):
    """Subset of 83:C9D7/CA8F for observed catalog ranges and state 0..2."""
    high, low = raw >> 4, raw & 15
    if high > 9 or state not in (0, 1, 2):
        raise ValueError('Outside audited range')
    field62, field66 = low, 9 - high
    delta = 2 * state - 4
    if delta < 0:
        field62 = max(0, field62 + delta)
        field66 = min(9, field66 - delta)
    return field62, field66


def audit(rom_path, asm_path, catalog_path):
    rom = rom_path.read_bytes()
    if hashlib.md5(rom).hexdigest() != '345ddedcd63412b9373dabb67c11fc05':
        raise ValueError('Expected headerless USA ROM')
    asm = asm_path.read_text(encoding='utf8')
    checks = {
        0x1c9fb: 'bd 00 00 29 0f 85 62 bd 00 00 20 74 ca 85 66 a9 09 38 e5 66 85 66 22 8f ca 83',
        0x1ca8f: 'bd 08 00 0a 38 e9 04 10 18 85 40 18 65 62 10 02 a9 00 85 62 a5 66 38 e5 40 c9 09 90 02 a9 09 85 66 6b',
    }
    for offset, hex_bytes in checks.items():
        expected = bytes.fromhex(hex_bytes)
        if rom[offset:offset + len(expected)] != expected:
            raise ValueError(f'Unexpected opcodes at {offset:06x}')
    for name in ('CODE_83C9D7:', 'CODE_83CA8F:', 'CODE_8488E1:', 'CODE_80DDBE:'):
        if name not in asm:
            raise ValueError('Missing disassembly label ' + name)
    catalog = json.loads(catalog_path.read_text(encoding='utf8'))
    players = [p for team in catalog['teams'] for p in team['players']]
    if len(players) != 720:
        raise ValueError('Unexpected catalog size')
    scenarios = {str(state): {'changed62': 0, 'changed66': 0, 'clamped62': 0, 'clamped66': 0} for state in (0, 1, 2)}
    for player in players:
        raw = bytes.fromhex(player['raw']['attributes_hex'])[0]
        for state in (0, 1, 2):
            value62, value66 = transform(raw, state)
            row = scenarios[str(state)]
            row['changed62'] += value62 != (raw & 15)
            row['changed66'] += value66 != 9 - (raw >> 4)
            row['clamped62'] += state < 2 and value62 == 0
            row['clamped66'] += state < 2 and value66 == 9
    # Independently check all combinations in the tested range, including clamps.
    for high in range(10):
        for low in range(16):
            assert transform((high << 4) | low, 0) == (max(0, low - 4), min(9, 13 - high))
            assert transform((high << 4) | low, 1) == (max(0, low - 2), min(9, 11 - high))
            assert transform((high << 4) | low, 2) == (low, 9 - high)
    return {'schema': 'issd-movement-attributes-static/v1',
            'rom_sha256': hashlib.sha256(rom).hexdigest(),
            'assembly_sha256': hashlib.sha256(asm.encode('utf8')).hexdigest(),
            'catalog_records': len(players), 'initialization': '83:C9D7..83:CA1B',
            'adjustment': '83:CA8F..83:CAB0', 'sample_consumer': '84:88E1 / 80:DDBE',
            'hypothetical_state_scenarios': scenarios,
            'limits': ['Static instruction audit, no emulated intervention or observed field values.',
                       'State values 0, 1 and 2 are hypothetical; other values are not modeled.',
                       'Meaning and lifetime of runtime byte +8 are not established.',
                       'Actor field consumption and browser physics are not fully mapped.',
                       'Native editor labels are interpretations; no ROM is distributed.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for arg in ('rom', 'assembly', 'catalog', 'output'):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    result = audit(args.rom, args.assembly, args.catalog)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: {result['catalog_records']} jogadores, 480 combinações sintéticas")
