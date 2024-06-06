import unittest
import dataclasses
from typing import Tuple

from meda.dataclass.dataclass import FeatureDataclass, get_feature
from meda.dataclass.feature import Feature


class SubClass(FeatureDataclass):
    foo: str = 'bar'


class ThisMustBePickleable(FeatureDataclass):
    subclass: SubClass
    bar: int = Feature(comment="m", input_key='')
    key: float = Feature(temporary=True)
    foo: str = Feature(default='abc')


class TestDataclassMeta(unittest.TestCase):
    def test_field_conversion(self):
        class SomeClass(FeatureDataclass):
            foo: str = 'bar'
            key: str = Feature(default="value")
            abar: str = "default"

        for f in dataclasses.fields(SomeClass):
            self.assertIsInstance(f, Feature)

        self.assertEqual({f.default for f in dataclasses.fields(SomeClass) if f.name != "foo"},
                         {"value", "default"})

    def test_frozen(self):
        class SomeClass(FeatureDataclass):
            foo: str = 'bar'

        sm = SomeClass(foo='ab')

        with self.assertRaises(dataclasses.FrozenInstanceError):
            sm.foo = 'bk'

    def test_plain_pickle(self):
        import pickle

        s = SubClass(foo='hello')
        t: SubClass = pickle.loads(pickle.dumps(s))

        self.assertEqual(s, t)
        self.assertEqual(type(s), type(t))
        self.assertIs(type(s), type(t))  # this tests the registry

        self.assertEqual(SubClass(foo='hello'), t)
        self.assertNotEqual(SubClass(foo='bar'), t)

        with self.assertRaises(dataclasses.FrozenInstanceError):
            s.foo = 8

        with self.assertRaises(dataclasses.FrozenInstanceError):
            t.foo = 8

    def test_nested(self):
        import pickle

        s = ThisMustBePickleable(foo='str', subclass=SubClass(foo='hello'), bar=1, key=1.)
        t = pickle.loads(pickle.dumps(s))

        self.assertEqual(s, t)
        self.assertEqual(type(s), type(t))
        self.assertIs(type(s), type(t))  # this tests the registry

        self.assertEqual(ThisMustBePickleable(foo='str', subclass=SubClass(foo='hello'), bar=1, key=1.), t)
        self.assertNotEqual(ThisMustBePickleable(foo='abc', subclass=SubClass(foo='hello'), bar=1, key=1.), t)

    def test_nested_pickle(self):
        import pickle

        s = ThisMustBePickleable(foo='B', bar=3, key=3.4, subclass=SubClass(foo=1))
        t = ThisMustBePickleable(foo='A', bar=3, key=3.4, subclass=SubClass(foo=1))

        self.assertEqual(s, pickle.loads(pickle.dumps(s)))
        self.assertEqual(t, pickle.loads(pickle.dumps(t)))

        self.assertNotEqual(s, t)
        self.assertNotEqual(pickle.loads(pickle.dumps(s)), pickle.loads(pickle.dumps(t)))

        self.assertEqual(1, s.subclass.foo, t.subclass.foo)

    def test_tuple(self):
        with self.subTest("valid-temporary-tuple"):
            class GoodAssessment(FeatureDataclass):
                weird: Tuple[str, int] = Feature(temporary=True)

    def test_tree(self):
        class SomeClass(FeatureDataclass):
            foo: str = 'bar'

        class SubClass(SomeClass):
            pass

        sc = SubClass(foo='ab')

        with self.assertRaises(dataclasses.FrozenInstanceError):
            sc.foo = 'bk'

        self.assertEqual(SomeClass.features, SubClass.features)
        self.assertIsNot(SomeClass.features, SubClass.features)

        self.assertEqual({"foo"}, {f.name for f in dataclasses.fields(SubClass)})
        self.assertEqual({"foo"}, {f.name for f in dataclasses.fields(SomeClass)})

    def test_defaults(self):
        with self.subTest("assign"):
            class SomeClass(FeatureDataclass):
                value: str = Feature(default='abc')

            self.assertEqual(SomeClass().value, 'abc')

        h = hash(SomeClass)

        with self.subTest("assign different"):
            class SomeClass(FeatureDataclass):
                value: str = Feature(default='abc', comment='foo')

            self.assertEqual(SomeClass().value, 'abc')

        self.assertNotEqual(h, hash(SomeClass))

    def test_temporary_and_compare(self):
        with self.assertRaises(TypeError):
            class TemporaryCompareDisallowed(FeatureDataclass):
                some_field: str = Feature(temporary=True, compare=True)

        class TemporaryNotCompare(FeatureDataclass):
            temp: str = Feature(temporary=True)
            field: str = 'abc'

        self.assertEqual(TemporaryNotCompare(field='abc', temp='def'),
                         TemporaryNotCompare(field='abc', temp='abc'))

        class NotTemporaryCompare(FeatureDataclass):
            field: str  = Feature(input_key='')

        self.assertEqual(NotTemporaryCompare(field='abc'), NotTemporaryCompare(field='abc'))
        self.assertNotEqual(NotTemporaryCompare(field='abc'), NotTemporaryCompare(field='def'))

    def test_comment(self):
        class UnitClass(FeatureDataclass):
            foo: int = Feature(comment='m', input_key='')

        u = UnitClass(foo=2)

        self.assertEqual('m', get_feature(type(u), 'foo').comment)
