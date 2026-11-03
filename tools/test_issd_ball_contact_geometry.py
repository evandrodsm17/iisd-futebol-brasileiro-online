import unittest
from issd_ball_contact_geometry import contact_carry


class ContactGeometryTest(unittest.TestCase):
    def check(self, **changes):
        args = dict(actor_x=158, actor_y=119, actor_z=0, ball_x=160, ball_y=121,
                    ball_z=0xfff9, field_3e=0, field_68=10, global_11fa=0,
                    actor_team=0x0d00, reference_team=0x0e00)
        args.update(changes)
        return contact_carry(**args)

    def test_observed_and_height_limit(self):
        self.assertEqual(self.check(), 0)
        self.assertEqual(self.check(ball_z=0xffe8), 1)
        self.assertEqual(self.check(ball_z=0xffe9), 0)

    def test_axis_boundaries(self):
        self.assertEqual(self.check(ball_x=146), 0)
        self.assertEqual(self.check(ball_x=145), 1)
        self.assertEqual(self.check(ball_x=169), 0)
        self.assertEqual(self.check(ball_x=170), 1)
        self.assertEqual(self.check(ball_y=111), 0)
        self.assertEqual(self.check(ball_y=110), 1)

    def test_gates_and_alternate_height(self):
        self.assertEqual(self.check(global_11fa=0x8000), 1)
        self.assertEqual(self.check(field_3e=1), 1)
        self.assertEqual(self.check(field_68=0, ball_z=0xffd0), 0)
        self.assertEqual(self.check(field_68=0, ball_z=0xffcf), 1)
        self.assertEqual(self.check(field_68=0, ball_z=1), 1)

    def test_invalid(self):
        with self.assertRaises(ValueError):
            self.check(actor_x=-1)

    def test_opposing_team_alternate_axis_limits(self):
        self.assertEqual(self.check(field_68=0, ball_x=144), 0)
        self.assertEqual(self.check(field_68=0, ball_x=143), 1)
        self.assertEqual(self.check(field_68=0, ball_x=171), 0)
        self.assertEqual(self.check(field_68=0, ball_x=172), 1)
        self.assertEqual(self.check(field_68=0, ball_y=109), 0)
        self.assertEqual(self.check(field_68=0, ball_y=108), 1)

    def test_adc_carry_at_word_wrap(self):
        self.assertEqual(self.check(actor_x=0xfffa, ball_x=6), 0)
        self.assertEqual(self.check(actor_x=0xfffa, ball_x=7), 1)
        self.assertEqual(self.check(actor_x=0xfffa, ball_x=0xffff), 0)


if __name__ == '__main__':
    unittest.main()
