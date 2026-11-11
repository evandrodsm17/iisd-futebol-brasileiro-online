import unittest
from audit_issd_goal_edge_velocity import expected_x, expected_y, signed

class VelocityBranches(unittest.TestCase):
 def test_y_direction_and_small_negative_fraction(self):
  self.assertEqual(signed(expected_y((-373)&0xffffffff,0x20)),93)
  self.assertEqual(signed(expected_y(373,0)), -93)
  self.assertEqual(signed(expected_y(373,0x20)),373)
  self.assertEqual(signed(expected_y((-373)&0xffffffff,0)),-373)
 def test_x_threshold_and_negation_rounding(self):
  self.assertEqual(signed(expected_x((-129953)&0xffffffff)),-129953)
  self.assertEqual(signed(expected_x((-131073)&0xffffffff)),-65536)
  self.assertEqual(signed(expected_x(131073)),65536)
  self.assertEqual(signed(expected_x(131071)),131071)
if __name__=='__main__':unittest.main()
