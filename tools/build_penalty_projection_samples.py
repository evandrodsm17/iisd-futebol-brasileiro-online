"""Build compact projection evidence from existing audited reports and local frame indexes."""
import hashlib
import json
from pathlib import Path

names = ('directional', 'intermediate-ball', 'large-ball')
reports = [json.loads(Path(f'docs/issd-penalty-{name}-projection.json').read_text(encoding='utf8')) for name in names]
root = Path('analysis/movement-progression-probe')
captures = []
for index in range(2):
    group = [report['captures'][index] for report in reports]
    if len({item['graphics_sha256'] for item in group}) != 1 or len({item['name'] for item in group}) != 1:
        raise ValueError('Mismatched projection captures')
    raw = (root / group[0]['name'] / 'graphics.jsonl').read_bytes()
    if hashlib.sha256(raw).hexdigest() != group[0]['graphics_sha256']:
        raise ValueError('Capture hash mismatch')
    samples = {item['frame']: item['delta'] - 1 for item in map(json.loads, raw.splitlines()) if item.get('type') == 'full_graphics'}
    if sorted(samples.values()) != list(range(40)):
        raise ValueError('Unexpected frame indices')
    frames = [None] * 40
    for capture, size in zip(group, (8, 8, 16)):
        for observed in capture['samples']:
            frame = samples[observed['frame']]
            candidates = [c for c in observed['candidates'] if c['lag'] == 2 and c['matches_both']]
            if len(candidates) != 1 or frames[frame] is not None:
                raise ValueError('Ambiguous projection sample')
            c = candidates[0]
            frames[frame] = {'x': c['object_x'], 'y': c['object_y'], 'height': c['object_height'],
                             'partX': c['offset_x'], 'partY': c['offset_y'], 'size': size,
                             'oamX': c['oam_x'], 'oamY': c['oam_y']}
    if sum(frame is not None for frame in frames) != 39:
        raise ValueError('Unexpected sample count')
    captures.append({'input': group[0]['input_direction'], 'graphics_sha256': group[0]['graphics_sha256'], 'frames': frames})
Path('dist/data/issd-penalty-projection-samples.json').write_text(json.dumps({'schema': 'issd-penalty-projection-samples/v1', 'captures': captures}, separators=(',', ':')) + '\n', encoding='utf8')
