import os.path
from typing import Union, Set
from pathlib import Path

import yaml


class UnitConverter:

    def __init__(self, yaml_file: str):
        """

        :param yaml_file: full path to yaml file
        """
        # load dimensions.yaml containing the conversions
        with open(file=yaml_file,
                  mode='r') as f:
            self._dimensions = yaml.safe_load(f)

        # add unity conversion factor for ref_unit
        for dim in self._dimensions.keys():
            self._dimensions[dim]['conversion'].update({self._dimensions[dim]['ref_unit']: 1})

        # validate that all conversion factors are numeric
        for dim in self._dimensions.keys():
            for unit, factor in self._dimensions[dim]['conversion'].items():
                if type(factor) not in {int, float}:
                    raise TypeError(f"Error: invalid type for factor {dim}, {unit}: {factor}")

    def __call__(self, value: Union[int, float],
                 dimension: str,
                 source_unit: str,
                 target_unit: str):
        # this function will transform the value from the source to target unit
        return value * self.transform_factor(dimension=dimension,
                                             source_unit=source_unit,
                                             target_unit=target_unit)

    def transform_factor(self, dimension: str, source_unit: str, target_unit: str) -> float:
        # multiplicative factor to transform a value from source to target unit
        conversion = self._dimensions[dimension]['conversion']
        return conversion[target_unit] / conversion[source_unit]

    def valid_unit(self, dimension: str, unit: str) -> bool:
        return unit in self._dimensions[dimension]['conversion'].keys()

    def allowed_units(self, dimension: str) -> Set[str]:
        return set(self._dimensions[dimension]['conversion'].keys())

    def ref_unit(self, dimension: str) -> str:
        return self._dimensions[dimension]['ref_unit']


unit_converter = UnitConverter(yaml_file=os.path.join(Path(__file__).parent, 'dimensions.yaml'))
