import copy
import unittest
from summarize_issd_action_matrix import summarize_trial


def row():
    return {'mode1': 6, 'mode2': 8, 'phase': 0, 'player_setting': 4,
            'selected_p1': 0x500, 'link_a4': 0, 'link_a6': 0,
            'ball': {'x': 0, 'y': 0, 'z': 0}, 'actors': [], 'controls': []}


class MatrixTests(unittest.TestCase):
    def test_rejects_different_baseline(self):
        a = {'samples': {i: row() for i in range(0, 486, 2)}}
        b = copy.deepcopy(a)
        for i in (480, 482, 484): a['samples'][i]['held_p2'] = 0x40
        a['samples'][2]['ball']['x'] = 1
        result = summarize_trial('X', a, b)
        self.assertFalse(result['comparison_eligible'])
        self.assertIsNone(result['first_ball_record_difference'])

    def test_accepts_comparable_input(self):
        a = {'samples': {i: row() for i in range(0, 486, 2)}}
        b = copy.deepcopy(a)
        for i in (480, 482, 484): a['samples'][i]['held_p2'] = 0x40
        a['samples'][482]['ball']['x'] = 1
        result = summarize_trial('X', a, b)
        self.assertTrue(result['comparison_eligible'])
        self.assertEqual(result['first_ball_record_difference'], 482)


if __name__ == '__main__': unittest.main()
