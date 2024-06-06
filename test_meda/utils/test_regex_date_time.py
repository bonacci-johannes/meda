import unittest

from meda.utils.regex_date_time import RegexDateTime


class TestRegexDateTime(unittest.TestCase):

    def test_extract_time(self):

        with self.subTest('test delimiter'):
            for delimiter in RegexDateTime._re_delimiter_time[1:-1]:
                self.assertEqual('20:12:04',
                                 RegexDateTime.extract_time(f'20{delimiter}12{delimiter}04').__str__())

        with self.subTest('test formats: hh:mm:ss, hh:mm, h:mm:ss and h:mm'):
            self.assertEqual('12:12:12', RegexDateTime.extract_time('12:12:12').__str__())
            self.assertEqual('11:11:00', RegexDateTime.extract_time('11:11').__str__())
            self.assertEqual('00:12:12', RegexDateTime.extract_time('0:12:12').__str__())
            self.assertEqual('00:11:00', RegexDateTime.extract_time('0:11').__str__())

        with self.subTest('test invalid formats'):
            self.assertRaises(ValueError, RegexDateTime.extract_time, '12:2')
            self.assertRaises(ValueError, RegexDateTime.extract_time, '12-12')

    def test_extract_date(self):
        with self.subTest('test delimiter'):
            for delimiter in RegexDateTime._re_delimiter_date[1:-1]:
                self.assertEqual('2012-12-12',
                                 RegexDateTime.extract_date(f'2012{delimiter}12{delimiter}12').__str__())

        with self.subTest('test formats: ymd and dmy'):
            self.assertEqual('2012-12-12', RegexDateTime.extract_date('12-12-2012').__str__())
            self.assertEqual('2012-12-12', RegexDateTime.extract_date('2012-12-12').__str__())

        with self.subTest('test year only'):
            self.assertEqual('2012-01-01', RegexDateTime.extract_date('2012').__str__())

        with self.subTest('test invalid date short'):
            self.assertRaises(ValueError, RegexDateTime.extract_date, '00_00_00')
            self.assertRaises(ValueError, RegexDateTime.extract_date, '00_0_00')
            self.assertRaises(ValueError, RegexDateTime.extract_date, '0_00_00')
            self.assertRaises(ValueError, RegexDateTime.extract_date, '0_0_00')
            self.assertEqual('2000-01-01', RegexDateTime.extract_date('xx.01.00').__str__())

        with self.subTest('test short forms'):
            self.assertEqual('2012-03-03', RegexDateTime.extract_date('2012.3.3').__str__())

        with self.subTest('test century short forms'):
            self.assertEqual('2012-03-03', RegexDateTime.extract_date('3.3.12').__str__())
            self.assertEqual('2012-03-01', RegexDateTime.extract_date('xx.3.12').__str__())
            self.assertEqual('2012-03-01', RegexDateTime.extract_date('xx-3-12').__str__())
            self.assertEqual('1952-03-01', RegexDateTime.extract_date('xx-3-52').__str__())
            self.assertEqual('1952-01-01', RegexDateTime.extract_date('xx.01.52').__str__())

        with self.subTest('test corrections'):
            self.assertEqual('2012-01-01', RegexDateTime.extract_date('2012.01.00').__str__())
            self.assertEqual('2012-01-01', RegexDateTime.extract_date('2012.01.0').__str__())

            self.assertEqual('2012-02-01', RegexDateTime.extract_date('2012.02.00').__str__())
            self.assertEqual('2012-02-01', RegexDateTime.extract_date('2012.02.0').__str__())
            self.assertEqual('2012-02-01', RegexDateTime.extract_date('2012.2.00').__str__())
            self.assertEqual('2012-02-01', RegexDateTime.extract_date('2012.2.0').__str__())

        with self.subTest('test invalid formats'):
            self.assertRaises(ValueError, RegexDateTime.extract_date, '12_12_2012')
            self.assertRaises(ValueError, RegexDateTime.extract_date, '12:12:2012')

    def test_extract_datetime(self):
        with self.subTest('test delimiter'):
            for delimiter in RegexDateTime._re_delimiter_datetime[1:-1]:
                self.assertEqual('2012-12-12 12:12:12',
                                 RegexDateTime.extract_datetime(f'2012-12-12{delimiter}12:12:12').__str__())

    def test_delimiter(self):
        d_time = set(RegexDateTime._re_delimiter_time[1:-1])
        d_date = set(RegexDateTime._re_delimiter_date[1:-1])
        d_datetime = set(RegexDateTime._re_delimiter_datetime[1:-1])

        with self.subTest('empty intersection'):
            error_msg = 'Error: intersections of delimiters should be empty'
            self.assertEqual(set(), set.intersection(d_time, d_date), msg=error_msg)
            self.assertEqual(set(), set.intersection(d_time, d_datetime), msg=error_msg)
            self.assertEqual(set(), set.intersection(d_date, d_datetime), msg=error_msg)

        with self.subTest('dash delimiter at end'):
            for delimiters in [RegexDateTime._re_delimiter_date,
                               RegexDateTime._re_delimiter_time,
                               RegexDateTime._re_delimiter_datetime]:
                self.assertFalse(('-' in delimiters) ^ (delimiters[-2] == '-'),
                                 msg=f'dash delimiter should be at the end. Delimiters: {delimiters}')
