"""Measure continuous per-frame actor descriptors from an automated replay."""
import argparse
import hashlib
import json
from pathlib import Path


def analyze(rows, actor_address, script, first, last):
    starts = [r for r in rows if r.get('type') == 'experiment_start']
    if len(starts) != 1: raise ValueError('Expected exactly one experiment start')
    trigger = starts[0]['step']
    samples = {r['step'] - trigger: r for r in rows if not r.get('type') and 'step' in r
               and first <= r['step'] - trigger <= last}
    if sorted(samples) != list(range(first, last + 1)):
        raise ValueError('Requested window is not sampled on every frame')
    track = []
    for elapsed, sample in sorted(samples.items()):
        actors = [a for a in sample['actors'] if a['address'] == actor_address]
        if len(actors) != 1: raise ValueError('Actor missing or duplicated')
        actor = actors[0]
        track.append((elapsed, sample['frame'], actor))
    if any(track[i][1] != track[i - 1][1] + 1 for i in range(1, len(track))):
        raise ValueError('Emulator frame numbers are not consecutive')
    runs = []
    for elapsed, frame, actor in track:
        key = (actor['script'], actor['direction'], actor['descriptor'])
        if not runs or runs[-1]['key'] != key:
            runs.append({'key': key, 'first_elapsed': elapsed, 'first_frame': frame, 'samples': 0})
        runs[-1]['samples'] += 1
    selected = []
    for index, run in enumerate(runs):
        if run['key'][0] != script: continue
        selected.append({'script': run['key'][0], 'direction': run['key'][1],
                         'descriptor': run['key'][2], 'first_elapsed': run['first_elapsed'],
                         'first_frame': run['first_frame'], 'observed_frames': run['samples'],
                         'start_observed': index > 0,
                         'end_observed': index < len(runs) - 1})
    return {'actor': actor_address, 'script': script, 'window': [first, last],
            'frames': len(track), 'runs': selected,
            'limitations': ['A measured hold requires observed start and end; boundary runs are lower bounds.',
                            'Actor metadata alone does not validate OAM composition or palettes.',
                            'Timing is specific to this replay and configuration.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('trace', type=Path)
    p.add_argument('--actor', type=lambda s: int(s, 0), required=True)
    p.add_argument('--script', type=lambda s: int(s, 0), required=True)
    p.add_argument('--first', type=int, required=True)
    p.add_argument('--last', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    raw = a.trace.read_bytes()
    result = analyze([json.loads(line) for line in raw.splitlines() if line.strip()],
                     a.actor, a.script, a.first, a.last)
    result.update({'schema': 'issd-replay-animation/v1',
                   'source': {'path': a.trace.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(),
                              'bytes': len(raw)}})
    a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('frames:', result['frames'], 'descriptor runs:', len(result['runs']))


if __name__ == '__main__': main()
