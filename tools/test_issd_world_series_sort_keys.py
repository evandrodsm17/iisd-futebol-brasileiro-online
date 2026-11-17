import unittest
from audit_issd_world_series_sort_keys import key


class SortKeyTests(unittest.TestCase):
    def test_fields_and_selected_offset(self):
        self.assertEqual(key(0x0100, 0, 2), 0x0200)
        self.assertEqual(key(0x0001, 2, 0), 0x0002)
        self.assertEqual(key(0x0100, 2, 2), 0x0201)
        self.assertGreater(key(0x0100, 0, 2), key(0x0001, 2, 0))

    def test_upper_bits_do_not_contribute(self):
        self.assertEqual(key(0xc0c0, 0, 2), 0)
        self.assertEqual(key(0xffff, 0, 0), 0x7e7f)


if __name__ == '__main__':
    unittest.main()
