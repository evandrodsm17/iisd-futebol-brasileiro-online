"""Compare isolated BizHawk routine observations to the extracted ROM table."""
import argparse
import json
from pathlib import Path


def verify(paths, manifest):
    teams = {team['team_id']: team for team in manifest['teams']}
    observations = []
    seen = set()
    for path in paths:
        for line in path.read_text(encoding='utf8').splitlines():
            row = json.loads(line)
            key = (row['team'], row['kit'])
            if row['kit'] not in (0, 1):
                raise ValueError(f'Invalid observation: {key}')
            entry = teams[row['team']]['home' if row['kit'] == 0 else 'away']
            expected = row['seed'] if entry['selector'] == 0 else entry['bgr555']
            if row['result'] != expected:
                raise ValueError(f'Palette mismatch for {key}: {row["result"]} != {expected}')
            if key in seen:
                continue
            seen.add(key)
            observations.append({'team': key[0], 'kit': key[1], 'selector': entry['selector'],
                                 'seed': row['seed'], 'result': row['result']})
    if len(observations) < 6 or not any(row['selector'] == 0 for row in observations):
        raise ValueError('Expected six distinct cases, including a no-write selector')
    return {'schema': 'issd-team-detail-synthetic-probe/v1', 'observations': observations,
            'limitations': ['Synthetic team and kit fields in isolated emulator RAM.',
                            'Routine output in palette mirror only; final PPU colors and player appearance are not validated.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('captures', type=Path, nargs='+')
    parser.add_argument('--manifest', type=Path, default=Path('dist/data/issd-team-detail-colors.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.captures, json.loads(args.manifest.read_text(encoding='utf8')))
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf8')
    print(f"Validated {len(report['observations'])} synthetic routine observations")
