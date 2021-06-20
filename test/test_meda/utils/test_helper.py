import unittest

from meda.utils.helper import camel_to_snake


class TestHelpers(unittest.TestCase):

    def test_camel_to_snake(self):
        self.assertEqual(camel_to_snake('AbAbb1A1b'), 'ab_abb_1_a_1b')
        self.assertEqual(camel_to_snake('1234'), '1_2_3_4')
        self.assertEqual(camel_to_snake('Abb_b_Ab_1_2b'), 'abb_b__ab__1__2b')
