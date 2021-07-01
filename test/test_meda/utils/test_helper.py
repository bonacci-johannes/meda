import unittest

from meda.utils.helper import camel_to_snake


class TestHelpers(unittest.TestCase):

    def test_camel_to_snake(self):
        self.assertEqual(camel_to_snake('AbAbb1A1b'), 'ab_abb_1_a_1_b')
        self.assertEqual(camel_to_snake('1234'), '1234')
        self.assertEqual(camel_to_snake('Sf12Freq'), 'sf_12_freq')
        self.assertEqual(camel_to_snake('Abb_b_Ab_1_2b'), 'abb_b_ab_1_2_b')
        self.assertEqual(camel_to_snake('__Abb____bAb_12b_'), 'abb_b_ab_12_b')
