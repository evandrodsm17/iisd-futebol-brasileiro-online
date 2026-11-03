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
    for line in raw.splitlines():
        if not line.strip(): continue
        row = json.loads(line)
        mirror = (path.parent / row['oam_mirror']).read_bytes()
        ppu = (path.parent / row['oam_ppu']).read_bytes() if row.get('oam_ppu') else None
        actor = row['actor']
        snapshots.append({'frame': row['frame'], 'step': row.get('step'),
                          'actor': actor['address'], 'script': actor['animation_script'],
                          'direction': actor['direction'], 'descriptor': actor['descriptor'],
                          'mirror_vs_ppu_differing_bytes': compare_oam(mirror, ppu) if ppu else None,
                          'has_screenshot': bool(row.get('screenshot'))})
    return {'schema': 'issd-graphics-replay-audit/v1',
            'source': {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest()},
            'validation': validation, 'snapshots': snapshots,
            'limitations': ['File integrity does not establish OAM-to-actor assignment.',
                            'Different mirror and PPU OAM contents require timing/association investigation.',
                            'CGRAM is a WRAM mirror; same-frame palette correspondence remains unverified.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    result = report(a.trace)
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('snapshots:', len(result['snapshots']))


if __name__ == '__main__': main()
