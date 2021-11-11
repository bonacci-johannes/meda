from datetime import date, timedelta
from datetime import datetime
from typing import Union, Dict, Optional, Any, Tuple

from meda.dataclass.dataclass import FeatureDataclass, FeatureDataclassMeta, UniqueCommonFeatureDataclass, \
    HeadSeriesFeatureDataclass, is_head_series_feature_dataclass, get_head_series_feature_dataclass, \
    is_nest_series_feature_dataclass, NestSeriesFeatureDataclass, is_series_dataclass_ident, SeriesDataclassIdent, \
    SeriesUniqueCommonFeatureDataclass, get_nested_keys, is_feature_dataclass_meta, get_nested_dataclass
from meda.dataclass.defaults import BooleanCases
from meda.dataclass.feature import Feature
from meda.dataclass.reflection import is_optional, get_nested_type, has_nested_type
from meda.utils.regex_date_time import RegexDateTime


class FeatureDataclassFactory:
    """
    todo: write a docu
    """
    value_fall_back = {bool: False,
                       bytes: b"112358",
                       int: -112358,
                       float: -112358.13,
                       str: '112358',
                       date: date(day=1, month=1, year=2358),
                       datetime: datetime(day=1, month=1, year=2358, hour=13, minute=21),
                       timedelta: timedelta(seconds=1)}

    @classmethod
    def _dataclass_fall_back(cls, data_class: FeatureDataclassMeta):
        kw_args = {}
        for field in data_class.features:
            if is_feature_dataclass_meta(field.type):
                kw_args.update({field.name: cls._dataclass_fall_back(get_nested_dataclass(field.type))})
            elif is_optional(field.type):
                kw_args.update({field.name: None})
            elif field.type in cls.value_fall_back.keys():
                kw_args.update({field.name: cls.value_fall_back[field.type]})
            else:
                raise ValueError(f'Error: no fall back value for type: {field.type}')
        return data_class(**kw_args)

    def __init__(self, boolean_cases: BooleanCases):
        self._boolean_cases = boolean_cases
        self._generator_errors = {}

    def generator(self,
                  feature_dataclass: FeatureDataclassMeta,
                  data_dict: Dict[str, str],
                  series_dataclass_key: Optional[str] = None) \
            -> Tuple[Optional[Union[FeatureDataclass, UniqueCommonFeatureDataclass]], Optional[str]]:
        # todo write a docu
        if issubclass(feature_dataclass, FeatureDataclass) and (series_dataclass_key is None):
            pass
        elif issubclass(feature_dataclass, HeadSeriesFeatureDataclass) and (type(series_dataclass_key) is str):
            pass
        elif issubclass(feature_dataclass, NestSeriesFeatureDataclass) and (type(series_dataclass_key) is str):
            pass
        else:
            raise ValueError(f"Error: series_dataclass_key should be a string for SeriesFeatureDataclass else None. "
                             + f"feature_dataclass={feature_dataclass} and series_dataclass_key={series_dataclass_key}")

        self._generator_errors = {}

        initialized_dataclass = self._generator(feature_dataclass=feature_dataclass,
                                                data_dict=data_dict,
                                                series_dataclass_key=series_dataclass_key)

        errors = self._get_generator_error(feature_dataclass=feature_dataclass,
                                           series_dataclass_key=series_dataclass_key)
        errors_str = None if errors is None else str(errors)

        return initialized_dataclass, errors_str

    @staticmethod
    def _has_error_field(feature_dataclass: FeatureDataclassMeta) -> bool:
        for field in feature_dataclass.features:
            if field.is_error_field:
                return True
        return False

    @staticmethod
    def _error_key(feature_dataclass: FeatureDataclassMeta,
                   series_dataclass_key: Optional[str] = None) -> str:
        return feature_dataclass.__name__ + ("" if series_dataclass_key is None else f"_{series_dataclass_key}")

    def _set_generator_error(self,
                             msg: str,
                             feature_dataclass: FeatureDataclassMeta,
                             series_dataclass_key: Optional[str] = None):
        self._generator_errors.update({self._error_key(feature_dataclass, series_dataclass_key): msg})

    def _get_generator_error(self,
                             feature_dataclass: FeatureDataclassMeta,
                             series_dataclass_key: Optional[str] = None) \
            -> Optional[str]:
        return self._generator_errors.get(self._error_key(feature_dataclass, series_dataclass_key))

    def _generator(self,
                   feature_dataclass: FeatureDataclassMeta,
                   data_dict: Dict[str, str],
                   series_dataclass_key: Optional[str] = None) \
            -> Optional[Union[FeatureDataclass, UniqueCommonFeatureDataclass]]:
        """
        todo: update return types
        todo: write a docu

        :param feature_dataclass:
        :param data_dict:
        :param series_dataclass_key:
        :return: initialized feature_dataclass and None for an empty class or in case of transform errors
        """

        class _Empty:
            """ A helper class to check if a value is assigned"""
            pass

        kwargs = {}
        """ the kwargs dictionary to initialize the feature_dataclass """
        error_dict = {}
        """ a dictionary catching all value transformation errors for feature_dataclass """
        none_cascade = False
        """
        if a value transformation for an non-optional field fails this should cascade,
        until we arrive at the first optional parent_dataclass
        """
        # todo: implement a none_cascade test
        # todo: it might be clever to implement a drop_in_case_of_error flag for optional features

        if is_series_dataclass_ident(feature_dataclass):
            return feature_dataclass(series_ident=series_dataclass_key)

        is_series_dataclass = issubclass(feature_dataclass, (HeadSeriesFeatureDataclass,
                                                             NestSeriesFeatureDataclass,
                                                             SeriesUniqueCommonFeatureDataclass))
        # todo: simplify above statement after introducing series meta class
        series_ident_field_name = None
        error_field: Optional[Feature] = None

        for field in feature_dataclass.features:
            # todo: implement test cases for all conversions
            if field.is_error_field:
                error_field = field
                continue
            value = _Empty
            error_msg: Optional[str] = None
            skip_error_fallback: bool = False

            # determine value string and the value type
            value_type: Any = get_nested_type(field.type) if has_nested_type(field.type) else field.type

            # determine the type associated value
            if field.temporary:
                value = None
            elif field.is_series_ident_field:
                value = int(series_dataclass_key) if value_type is int else series_dataclass_key
                if series_ident_field_name is None:
                    series_ident_field_name = field.name
                else:
                    raise ValueError(f"multiple series_ident_field definitions for dataclass {feature_dataclass}")
            elif field.transformer is not None:
                data_keys = dict(field.input_key)[series_dataclass_key] if is_series_dataclass else field.input_key
                value_tuple = tuple(data_dict[key] for key in data_keys)
                try:
                    value = field.transformer(*value_tuple)
                except:
                    error_msg = f"Transformer failed for {field.name} with input={value_tuple}"
            elif (
                    is_series_dataclass_ident(value_type)
                    or ((type(value_type) is FeatureDataclassMeta)
                        and issubclass(value_type, UniqueCommonFeatureDataclass))
                    or ((type(value_type) is FeatureDataclassMeta) and issubclass(value_type, FeatureDataclass))
                    or (is_nest_series_feature_dataclass(field.type) and is_series_dataclass)
            ):
                skip_error_fallback = True
                value = self._generator(feature_dataclass=value_type,
                                        data_dict=data_dict,
                                        series_dataclass_key=series_dataclass_key)

                error_msg = self._get_generator_error(feature_dataclass=value_type,
                                                      series_dataclass_key=series_dataclass_key)
            elif (not is_series_dataclass and issubclass(value_type, (HeadSeriesFeatureDataclass,
                                                                      NestSeriesFeatureDataclass,
                                                                      SeriesUniqueCommonFeatureDataclass))):
                skip_error_fallback = True
                value = [self._generator(feature_dataclass=value_type,
                                         data_dict=data_dict, series_dataclass_key=key)
                         for key in get_nested_keys(value_type)]
                value = tuple([t for t in value if t is not None])

                error_msgs = [msg for msg in [self._get_generator_error(feature_dataclass=value_type,
                                                                        series_dataclass_key=key)
                                              for key in get_nested_keys(value_type)]
                              if msg is not None]
                if len(error_msgs) > 0:
                    error_msg = '{' + ', '.join([str(msg) for msg in error_msgs]) + '}'
            else:
                # determine value string
                if is_series_dataclass and (series_dataclass_key not in dict(field.input_key).keys()):
                    value_str = None
                else:
                    data_key = dict(field.input_key)[series_dataclass_key] if is_series_dataclass else field.input_key
                    value_str = data_dict[data_key]

                # transform value string to value of its type
                if value_str is None:
                    value = None
                elif (field.null_defaults is not None) and (value_str in field.null_defaults):
                    # handle optional cases for all value types via field.null_defaults
                    value = None
                elif value_type is str:
                    value = value_str
                elif value_type is bool:
                    # note that the optional case is already handled above
                    if value_str in self._boolean_cases.true:
                        value = True
                    elif value_str in self._boolean_cases.false:
                        value = False
                    else:
                        error_msg = f"Unknown boolean value: {value_str}"
                elif value_type is date:
                    try:
                        value = RegexDateTime.extract_date(value_str)
                    except:
                        error_msg = f"Invalid date: {value_str}"
                elif value_type is datetime:
                    try:
                        value = RegexDateTime.extract_datetime(value_str)
                    except:
                        error_msg = f"Invalid datetime: {value_str}"
                elif value_type is int or value_type is float:
                    # todo: implement a test case handling '<' or '>'
                    if value_str.count('>') == 1:
                        value_str = value_str.replace('>', '')
                    elif value_str.count('<') == 1:
                        value_str = value_str.replace('<', '')

                    if value_type is float:
                        if value_str.count(',') == 1 and value_str.count('.') == 0:
                            value_str = value_str.replace(',', '.')
                    try:
                        value = value_type(value_str)
                    except:
                        error_msg = f"Invalid numeric: {value_str}"
                else:
                    raise ValueError(f"handle file type: {value_type}")

            # managing the behavior in case of error with fall back for value
            if error_msg is not None:
                error_dict.update({field.name + (f"_{series_dataclass_key}" if is_series_dataclass else ""): error_msg})
                if not skip_error_fallback:
                    if is_optional(field.type):
                        value = None
                    else:
                        if isinstance(value_type, FeatureDataclassMeta):
                            value = self._dataclass_fall_back(value_type)
                        else:
                            value = self.value_fall_back[value_type]
                        none_cascade = True

            # check if value is assigned otherwise raise
            if value is _Empty:
                raise ValueError(f"no value assigned for field {field}")

            # update the kwargs dict
            kwargs.update({field.name: value})

        # update the global error handling fields
        if error_field is not None:
            kwargs.update({error_field.name: str(error_dict) if len(error_dict) > 0 else None})
        if len(error_dict) > 0:
            self._set_generator_error(msg=str(error_dict),
                                      feature_dataclass=feature_dataclass,
                                      series_dataclass_key=series_dataclass_key)

        ################
        # return cases #
        ################
        if none_cascade:
            # data is dropped due to transformation errors
            return None

        # return None for empty result set
        kw_values = []
        for key, val in kwargs.items():
            if not (isinstance(val, SeriesDataclassIdent)
                    or (key == series_ident_field_name)):
                kw_values.append(val)
        if set(kw_values) == {None}:
            return None

        # return initialized dataclass
        return feature_dataclass(**kwargs)
