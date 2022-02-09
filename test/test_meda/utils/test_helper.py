import unittest

from meda.utils.helper import camel_to_snake, numeric_type_of_string, string_to_numeric


class TestHelpers(unittest.TestCase):

    def test_camel_to_snake(self):
        self.assertEqual(camel_to_snake('AbAbb1A1b'), 'ab_abb_1_a_1_b')
        self.assertEqual(camel_to_snake('1234'), '1234')
        self.assertEqual(camel_to_snake('Sf12Freq'), 'sf_12_freq')
        self.assertEqual(camel_to_snake('Abb_b_Ab_1_2b'), 'abb_b_ab_1_2_b')
        self.assertEqual(camel_to_snake('__Abb____bAb_12b_'), 'abb_b_ab_12_b')

    def test_numeric_type_of_string(self):
        self.assertEqual(int, numeric_type_of_string('234'))
        self.assertEqual(float, numeric_type_of_string('2.34'))
        self.assertEqual(float, numeric_type_of_string('2,34'))
        self.assertEqual(str, numeric_type_of_string('2,,34'))
        self.assertEqual(str, numeric_type_of_string('2,.34'))

    def test_string_to_numeric(self):
        self.assertEqual(234, string_to_numeric('234'))
        self.assertEqual(2.34, string_to_numeric('2.34'))
        self.assertEqual(2.34, string_to_numeric('2,34'))
        self.assertEqual('2,,34', string_to_numeric('2,,34'))
        self.assertEqual('2,.34', string_to_numeric('2,.34'))
