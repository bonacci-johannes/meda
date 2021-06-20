import unittest
import pickle

from meda.dataclass.dataclass import SeriesDataclassIdent, dynamic_series_ident_cls, dynamic_series_ident


class SubClass(SeriesDataclassIdent):
    pass


class TestSeriesDataclassIdent(unittest.TestCase):
    def test_field_conversion(self):
        pass

    def test_equality(self):
        class Ident(SeriesDataclassIdent):
            pass

        self.assertEqual(Ident, dynamic_series_ident_cls(cls_name=Ident.__name__))
        self.assertTrue(Ident == dynamic_series_ident_cls(cls_name=Ident.__name__))
        self.assertFalse(Ident == dynamic_series_ident_cls(cls_name=Ident.__name__ + '_'))

        ident_1_s1 = Ident(series_ident='1')
        ident_1_d1 = dynamic_series_ident(cls_name=Ident.__name__, ident='1')
        ident_1_d2 = dynamic_series_ident(cls_name=Ident.__name__ + '_', ident='1')

        ident_2_s1 = Ident(series_ident='2')
        ident_2_d1 = dynamic_series_ident(cls_name=Ident.__name__, ident='2')

        self.assertTrue(ident_1_s1 == ident_1_d1)
        self.assertFalse(ident_1_s1 == ident_1_d2)
        self.assertFalse(ident_1_d1 == ident_1_d2)
        self.assertFalse(ident_1_s1 == ident_2_s1)
        self.assertFalse(ident_1_d1 == ident_2_d1)

        self.assertTrue(ident_1_d1.__eq__(ident_1_s1))
        self.assertTrue(ident_1_d1.__eq__(ident_1_d1))

    def test_picklable(self):
        ident_cls = dynamic_series_ident_cls(cls_name='Test')
        ident = ident_cls(series_ident='test_1')
        self.assertEqual(ident_cls.__name__, 'Test')
        self.assertEqual(ident, pickle.loads(pickle.dumps(ident)))
        self.assertTrue(pickle.loads(pickle.dumps(ident)).__eq__(ident))
