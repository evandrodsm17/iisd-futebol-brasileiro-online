"""Audit matching-frame replay artifacts without assigning OAM slots to an actor."""
import argparse
import hashlib
import json
from pathlib import Path

from validate_issd_native_action_oam import validate


def compare_oam(mirror, ppu):
    if len(mirror) != 544 or len(ppu) != 544:
        raise ValueError('Expected two 544-byte OAM captures')
    normalized = mirror[:512][::-1] + mirror[512:]
    return sum(a != b for a, b in zip(normalized, ppu))


def report(path):
    validation = validate(path)
    if not validation['valid']: raise ValueError('Invalid capture: ' + '; '.join(validation['errors']))
    raw = path.read_bytes()
    snapshots = []
    observations = []
    for line in raw.splitlines():
        if not line.strip(): continue
        row = json.loads(line)
        mirror = (path.parent / row['oam_mirror']).read_bytes()
        ppu = (path.parent / row['oam_ppu']).read_bytes() if row.get('oam_ppu') else None
        ppu_cgram = (path.parent / row['cgram_ppu']).read_bytes() if row.get('cgram_ppu') else None
        mirror_cgram = bytes.fromhex((path.parent / row['cgram']).read_text(encoding='utf-8'))
        if ppu_cgram is not None and len(ppu_cgram) != 512:
            raise ValueError('PPU CGRAM must be 512 bytes')
        actor = row['actor']
        snapshots.append({'frame': row['frame'], 'step': row.get('step'),
                          'actor': actor['address'], 'script': actor['animation_script'],
                          'direction': actor['direction'], 'descriptor': actor['descriptor'],
                          'mirror_vs_ppu_differing_bytes': compare_oam(mirror, ppu) if ppu else None,
                          'cgram_mirror_vs_ppu_differing_bytes': sum(a != b for a, b in zip(mirror_cgram, ppu_cgram)) if ppu_cgram else None,
                          'has_screenshot': bool(row.get('screenshot'))})
        observations.append({'frame': row['frame'], 'mirror': mirror, 'ppu': ppu,
                             'cgram_mirror': mirror_cgram, 'cgram_ppu': ppu_cgram})
    offsets = []
    for offset in (-2, -1, 0, 1, 2):
        pairs = [(a, b) for a in observations for b in observations
                 if b['frame'] == a['frame'] + offset and b['ppu'] is not None]
        differences = [compare_oam(a['mirror'], b['ppu']) for a, b in pairs]
        offsets.append({'ppu_frame_offset': offset, 'pairs': len(differences),
                        'exact_matches': sum(x == 0 for x in differences),
                        'total_differing_bytes': sum(differences)})
    cgram_offsets = []
    for offset in (-2, -1, 0, 1, 2):
        pairs = [(a, b) for a in observations for b in observations
                 if b['frame'] == a['frame'] + offset and b['cgram_ppu'] is not None]
        differences = [sum(x != y for x, y in zip(a['cgram_mirror'], b['cgram_ppu'])) for a, b in pairs]
        cgram_offsets.append({'ppu_frame_offset': offset, 'pairs': len(differences),
                              'exact_matches': sum(x == 0 for x in differences),
                              'total_differing_bytes': sum(differences)})
    return {'schema': 'issd-graphics-replay-audit/v1',
            'source': {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()},
            'validation': validation, 'snapshots': snapshots, 'oam_frame_offsets': offsets,
            'cgram_frame_offsets': cgram_offsets,
            'limitations': ['File integrity does not establish OAM-to-actor assignment.',
                            'Different mirror and PPU OAM contents require timing/association investigation.',
                            'CGRAM mirror comparison, when available, does not validate screenshot timing or palette use.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    result = report(a.trace)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('snapshots:', len(result['snapshots']))


if __name__ == '__main__': main()
