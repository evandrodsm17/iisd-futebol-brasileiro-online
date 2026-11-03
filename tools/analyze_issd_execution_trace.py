"""Summarize execute hooks without attributing events to an actor."""
import argparse
import hashlib
import json
from pathlib import Path


EMPTY_GUID = '00000000-0000-0000-0000-000000000000'


def summarize(rows):
    hooks, events = [], []
    start = end = trigger = None
    for row in rows:
        kind = row.get('type')
        if kind == 'hook_registration':
            handle = row.get('handle')
            hooks.append({'address': row['address'], 'registered': bool(
                row.get('success') and handle and handle != EMPTY_GUID)})
        elif kind == 'execution':
            events.append({k: row.get(k) for k in
                           ('step', 'frame', 'address', 'dp', 'a', 'x', 'y',
                            'ball_type', 'link_a6')})
        elif kind == 'session_start': start = row
        elif kind == 'session_end': end = row
        elif kind == 'experiment_start': trigger = row
    return {'hooks': hooks, 'events': events,
            'session_complete': bool(start and end and end.get('reason') == 'experiment_window_complete'),
            'experiment_start': trigger,
            'limitations': ['Callbacks observe all actors; without a direct-page register, actor attribution is not established.',
                            'Execution order alone does not establish player input semantics.',
                            'Values in callbacks are sampled before the instrumented instruction.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    digest = hashlib.sha256()
    def rows():
        with args.trace.open('rb') as stream:
            for line in stream:
                digest.update(line)
                if line.strip(): yield json.loads(line)
    result = summarize(rows())
    result['schema'] = 'issd-execution-trace-summary/v1'
    result['source'] = {'path': args.trace.as_posix(), 'sha256': digest.hexdigest(),
                        'bytes': args.trace.stat().st_size}
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('registered:', sum(h['registered'] for h in result['hooks']),
          'events:', len(result['events']), 'complete:', result['session_complete'])


if __name__ == '__main__': main()
