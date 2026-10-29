"""Summarize passive constraint samples without inferring executed branches."""
import argparse
from collections import Counter
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    samples = 0
    first = previous = last = None
    gaps = 0
    controls, phases, stadiums, counts = Counter(), Counter(), Counter(), Counter()
    anchor_frames = limit_mismatches = 0
    dimensions = [(1792,576),(1856,640),(1984,704),(2048,640),(1920,640),(1920,576),(1792,704),(2176,704)]
    with args.trace.open(encoding='utf-8') as stream:
        for line in stream:
            record = json.loads(line)
            if record.get('type') == 'session_start':
                continue
            frame, globals_, actors = record['frame'], record['globals'], record['actors']
            if first is None:
                first = frame
            if previous is not None and frame != previous + 1:
                gaps += 1
            previous = last = frame
            samples += 1
            counts[len(actors)] += 1
            controls[globals_['12FA']] += 1
            phases[globals_['00C0']] += 1
            selector = globals_['0086']
            stadiums[selector] += 1
            anchor_frames += any(actor['words']['006C'] & 0x0800 for actor in actors)
            if 0 <= selector < 8:
                w, h = dimensions[selector]
                expected = {'12A2':w,'12A4':h,'12E0':h+24,'12E2':w+128,'12E4':h//2-48,'12E6':h//2+48,'12E8':65480,'12EA':w+56}
                limit_mismatches += any(globals_[key] != value for key, value in expected.items())
    payload = {'source': str(args.trace), 'samples': samples, 'first_frame': first, 'last_frame': last,
               'nonconsecutive_frame_pairs': gaps, 'actor_counts': dict(counts), 'control_word_counts': dict(controls),
               'phase_counts': dict(phases), 'stadium_counts': dict(stadiums), 'frames_with_anchor_flag': anchor_frames,
               'dimension_limit_mismatch_frames': limit_mismatches,
               'limitations': ['Frame-end snapshots do not prove which internal branches executed.', 'Duration in seconds assumes 60 emulated frames per second.']}
    args.output.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
