import unittest
from analyze_issd_replay_animation import analyze


def sample(step, script, descriptor):
    return {'step': step, 'frame': step + 10, 'actors': [
        {'address': 0x1900, 'script': script, 'direction': 0, 'descriptor': descriptor}]}


class ReplayAnimationTests(unittest.TestCase):
    def test_measures_transition_and_end(self):
        rows = [{'type': 'experiment_start', 'step': 100}, sample(100, 1, 3),
                sample(101, 2, 4), sample(102, 2, 4), sample(103, 2, 5), sample(104, 1, 3)]
        result = analyze(rows, 0x1900, 2, 0, 4)
        self.assertEqual([r['observed_frames'] for r in result['runs']], [2, 1])
        self.assertTrue(all(r['start_observed'] and r['end_observed'] for r in result['runs']))

    def test_rejects_sampling_gap(self):
        rows = [{'type': 'experiment_start', 'step': 100}, sample(100, 2, 4), sample(102, 2, 4)]
        with self.assertRaises(ValueError): analyze(rows, 0x1900, 2, 0, 2)


if __name__ == '__main__': unittest.main()
