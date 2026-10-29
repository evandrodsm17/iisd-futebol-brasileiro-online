"""Compare consecutive native snapshots; matches are arithmetic, not causal proof."""
import argparse
from collections import Counter
import json
from pathlib import Path


def word_pair(words, low, high):
    return words[low] | (words[high] << 16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    previous = None
    counts = Counter()
    for line in args.trace.open(encoding='utf-8'):
        sample = json.loads(line)
        if 'actors' not in sample:
            continue
        if previous and sample['frame'] == previous['frame'] + 1:
            old = {actor['address']: actor['words'] for actor in previous['actors']}
            for actor in sample['actors']:
                if actor['address'] not in old:
                    continue
                before, after = old[actor['address']], actor['words']
                counts['actor_frame_pairs'] += 1
                moved = any(word_pair(before, lo, hi) != word_pair(after, lo, hi) for lo, hi in [('0006','0008'),('000A','000C')])
                if not moved:
                    counts['stationary_pairs'] += 1
                    continue
                counts['moving_pairs'] += 1
                for label, delta in [('previous_delta',before),('current_delta',after)]:
                    match = all(
                        (word_pair(before, lo, hi) + word_pair(delta, dlo, dhi)) & 0xffffffff == word_pair(after, lo, hi)
                        for lo, hi, dlo, dhi in [('0006','0008','0022','0024'),('000A','000C','0026','0028')])
                    counts[label + ('_exact' if match else '_different')] += 1
        previous = sample
    result = {'source':str(args.trace),'counts':dict(counts),'limitations':[
        'Only consecutive frame-end snapshots are compared; internal execution order is not observed.',
        'Stationary pairs are excluded from match counts to avoid counting zero-motion agreement.',
        'This checks native word arithmetic, not Canvas scale, speed, or full browser fidelity.',
        'Differences may include boundaries, collision, state changes, or updates within the frame; no cause is assigned.'
    ]}
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
