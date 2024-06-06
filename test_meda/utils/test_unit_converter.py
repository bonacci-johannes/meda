import unittest

from meda.utils.unit_conversion.unit_converter import unit_converter


class TestUnitConverter(unittest.TestCase):

    def test_converter(self):
        self.assertEqual(0.1,
                         unit_converter.transform_factor(dimension='density',
                                                         source_unit='mg/L',
                                                         target_unit='mg/dL'))

        self.assertEqual(1000,
                         unit_converter.transform_factor(dimension='density',
                                                         source_unit='g/L',
                                                         target_unit='mg/L'))

        self.assertEqual(0.1,
                         unit_converter(value=1.0,
                                        dimension='density',
                                        source_unit='mg/L',
                                        target_unit='mg/dL'))

        self.assertEqual(1000,
                         unit_converter(value=1.0,
                                        dimension='density',
                                        source_unit='g/L',
                                        target_unit='mg/L'))

    def test_scientific_number(self):
        self.assertEqual(1e6,
                         unit_converter.transform_factor(dimension='molar_density',
                                                         source_unit='mol/L',
                                                         target_unit='µmol/L'))
        self.assertEqual(1e12,
                         unit_converter.transform_factor(dimension='molar_density',
                                                         source_unit='mol/L',
                                                         target_unit='pmol/L'))

    def test_unit_converter(self):
        dimension = 'density'
        source_unit = 'g/L'
        target_unit = 'mg/L'

        self.assertEqual(unit_converter.transform_factor(dimension, source_unit, target_unit),
                         unit_converter.transform_factor(dimension, source_unit, target_unit))
