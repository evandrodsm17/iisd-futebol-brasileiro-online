"""Join existing audited geometry, decision and contact reports for one replay."""
import argparse
import hashlib
import json
from pathlib import Path


def audit(geometry_path, resolution_path, contact_path):
    sources = [geometry_path, resolution_path, contact_path]
    raw = [p.read_bytes() for p in sources]
    geometry, resolution, contact = [json.loads(data) for data in raw]
    expected = ['issd-penalty-goal-geometry/v1', 'issd-penalty-resolution-path/v1', 'issd-penalty-contact/v1']
    if [x['schema'] for x in (geometry, resolution, contact)] != expected:
        raise ValueError('Unexpected source reports')
    if resolution['trace_sha256'] != contact['hooks_sha256']:
        raise ValueError('Resolution and contact do not share the same capture')
    results = []
    for item in geometry['crossings']:
        if item['goal_branch']:
            continue
        matching = [entry for entry in resolution['results'] if entry['frame'] == item['frame']]
        if len(matching) != 1:
            raise ValueError('Missing resolution')
        route = matching[0]
        if (item['side'], item['round']) != (route['side'], route['round']) or route['goal_branch']:
            raise ValueError('Mismatched replay context')
        linked = [case for case in contact['cases'] if case['deferred_final']['frame'] == item['frame']]
        if route['deferred_finalize']:
            if item['model_applicable'] or len(linked) != 1:
                raise ValueError('Missing deferred contact')
            kind = 'deferred_contact'
        elif not item['model_applicable'] or linked:
            raise ValueError('Unexpected geometry/contact route')
        elif item['x'] < 0x18 or item['x'] >= 0xe0:
            kind = 'native_x_limit'
        elif 0x8000 <= item['height'] < 0xffb8:
            kind = 'native_height_limit'
        else:
            raise ValueError('No native comparison explains this branch')
        results.append({'frame': item['frame'], 'side': item['side'], 'round': item['round'],
                        'native_x': item['x'], 'native_y': item['y'], 'native_height': item['height'],
                        'route': kind, 'winner_branch': route['winner_branch']})
    if len(results) != 5 or [x['route'] for x in results].count('deferred_contact') != 3:
        raise ValueError('Unexpected recorded results')
    return {'schema': 'issd-penalty-miss-paths/v1',
            'sources': [{'file': p.name, 'sha256': hashlib.sha256(data).hexdigest()} for p, data in zip(sources, raw)],
            'results': results,
            'limits': ['One deterministic synthetic replay and related instrumented repetitions.',
                       'Contact was visually identified as goalkeeper action in the source audit; this is not a universal contact classification.',
                       'Native coordinates and height are not mapped to browser units or visual direction.',
                       'The score branch is not a complete classification for all possible penalty outcomes.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    for name in ('geometry', 'resolution', 'contact', 'output'):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    result = audit(args.geometry, args.resolution, args.contact)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf8')
    print(f"OK: {len(result['results'])} non-scoring routes correlated")
