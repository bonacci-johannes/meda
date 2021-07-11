import dataclasses
import datetime
from typing import Tuple, Type, Optional, Set
import inspect

from meda.dataclass.feature import Feature
from meda.dataclass.reflection import get_nested_type, is_mapping_str_to_any, is_tuple, has_nested_type, \
    is_optional, get_type


# todo: implement an annotation checker for dataclasses on init instance. Otherwise we can get some strange behavior.
# todo: check if implemented structure is allowed


class ExternMixin:
    """ A Mixin to indicate, that this class is initialized by a transformer"""
    pass


class FeatureDataclassMeta(type):
    """
    todo: update docu
    This metaclass provides hashing and comparing functionality for dataclasses with fields and features (fields with
    units.

    It may be used to cross-version type comparison of FeatureDataclass classes.
    """
    base_data_types = {int, float, str, bytes, bool, datetime.date, datetime.datetime, datetime.timedelta}

    def __init__(cls, *args, **kwargs):
        # todo: implement test cases for all raises
        super().__init__(*args, **kwargs)

        annotations = args[2].get("__annotations__", {})

        for key, value in cls.__dict__.items():
            if isinstance(value, Feature) and key in annotations:
                continue
            elif key in annotations:
                annotated_type = annotations[key]
                annotated_types = (get_nested_type(annotated_type), type(None)) \
                    if is_optional(annotated_type) else (annotated_type,)
                if (type(value) is int) and (annotated_types[0] is float):
                    # convert 'foo: float = 2' to 'foo: float = 2.0'
                    value = float(value)
                if isinstance(value, annotated_types):
                    setattr(cls, key, Feature(default=value))  # converts foo: str = 'some string'
                    continue
                else:
                    raise TypeError(f"Value type does not match the annotation for {key}")
            elif key[:2] != '__':
                raise TypeError(f"Error: No annotation provided for {key}")

        # Handle fields without an assigned feature
        # assign empty feature fields if field is a FeatureDataclass
        for name in (set(annotations.keys()) - set(cls.__dict__.keys())):
            annotation = annotations[name]
            annotated_type = get_nested_type(annotation) if has_nested_type(annotation) else annotation
            if isinstance(annotated_type, FeatureDataclassMeta):
                setattr(cls, name, Feature())
            elif issubclass(cls, ExternMixin):
                setattr(cls, name, Feature())
            else:
                raise TypeError(f"Error: The field {name} is not a feature or a FeatureDataclass")

        dataclasses.dataclass(cls, frozen=True)
        cls.features: Tuple[Feature] = dataclasses.fields(cls)

        # A loop to validate all features
        for field in cls.features:
            # get the value type
            value_type = get_nested_type(field.type) if has_nested_type(field.type) else field.type

            # skip temporary, json, feature_dataclass fields and raise if tuple
            if (field.temporary
                    or is_mapping_str_to_any(value_type)
                    or isinstance(value_type, FeatureDataclassMeta)):
                continue
            elif field.is_error_field:
                field_type = get_type(field.type)
                if field_type is str and is_optional(field.type):
                    continue
                else:
                    raise TypeError(f"The type of the series ident field {field} is not a str or not optional.")
            elif field.is_series_ident_field:
                field_type = get_type(field.type)
                if (field_type is str) or (field_type is int):
                    continue
                else:
                    raise TypeError(f"The type of the series ident field {field} is neither a str nor int.")
            elif is_tuple(field.type):
                raise TypeError(f"The field {field} is a tuple field. Tuple fields are not supported")

            # check conditions on feature arguments
            if (is_optional(field.type) and not any([isinstance(value_type, FeatureDataclassMeta),
                                                     issubclass(cls, ExternMixin),
                                                     field.transformer is not None,
                                                     field.null_defaults is not None])):
                # here we check when the field might be optional
                raise KeyError(f"Error: field={field.name} of dataclass={cls.__name__} is optional, "
                               + f"but neither a transformer or a null_set is provided ")
            elif (field.input_key is None) and not any([isinstance(value_type, FeatureDataclassMeta),
                                                        issubclass(cls, ExternMixin),
                                                        field.default is not dataclasses.MISSING]):
                # here we check when the field input_key might be optional
                raise KeyError(f"Error: input_key missing for field {field.name} in dataclass {cls.__name__}")

            # check value type
            if value_type in cls.base_data_types:
                pass
            elif isinstance(value_type, FeatureDataclassMeta):
                pass
            else:
                raise TypeError(f"Error: The field={field} of type={value_type} "
                                + "is neither a supported data type nor a DataclassMeta instance.")

    def __eq__(cls, other):
        if hasattr(other, '__name__') and hasattr(other, 'features'):
            return cls.__name__ == other.__name__ and cls.features == other.features
        else:
            return False

    def __hash__(cls):
        return hash(cls.__name__) * hash(cls.features)


class FeatureDataclass(metaclass=FeatureDataclassMeta):
    pass


class UniqueCommonFeatureDataclass(metaclass=FeatureDataclassMeta):
    """
    Usage:
    This dataclass can typically be used for configurations or possible answers of questionnaires

    Dataclass properties:
    - N -> 1 relationship: Other tables may have an foreign-key link to this table
    - all data-fields should full fill an unique constraint
    """
    pass


class SeriesDataclassIdent(UniqueCommonFeatureDataclass):
    series_ident: Optional[str] = None

    def __reduce__(self):
        """
        this function is called by pickle to make dynamically created classes pickable
        https://stackoverflow.com/a/11493777
        https://docs.python.org/3/library/pickle.html#object.__reduce__
        """
        return dynamic_series_ident, (self.__class__.__name__, self.series_ident)

    def __eq__(self, other):
        return all([isinstance(other, SeriesDataclassIdent),
                    self.__class__.__name__ == other.__class__.__name__,
                    self.series_ident == other.series_ident])


def dynamic_series_ident_cls(cls_name: str) -> SeriesDataclassIdent:
    # we have to include the __eq__ function here. Otherwise it will be 'NotImplemented'
    return type(cls_name, (SeriesDataclassIdent,), {'__eq__': SeriesDataclassIdent.__eq__})


def dynamic_series_ident(cls_name: str, ident: str) -> SeriesDataclassIdent:
    cls = dynamic_series_ident_cls(cls_name=cls_name)
    return cls(series_ident=ident)


class NestSeriesFeatureDataclassMeta(FeatureDataclassMeta):
    pass


class HeadSeriesFeatureDataclassMeta(NestSeriesFeatureDataclassMeta):
    def __init__(cls, *args, **kwargs):
        """dynamically creation of an ident feature class"""
        series_ident_field = 'series_ident'
        if '__annotations__' in args[2]:
            series_ident_cls = dynamic_series_ident_cls(cls_name=cls.__name__ + 'Ident')
            args[2]['__annotations__'].update({series_ident_field: Optional[series_ident_cls]})
            setattr(cls, series_ident_field, None)
        super().__init__(*args, **kwargs)


class SeriesUniqueCommonFeatureDataclass(UniqueCommonFeatureDataclass):
    # todo: consider a check on features via metaclass
    pass


class NestSeriesFeatureDataclass(metaclass=NestSeriesFeatureDataclassMeta):
    # todo: Metaclass: Check that non-optional features implement the same keys, also subclasses
    # todo: Metaclass: Check that sub_dataclasses are of type SeriesFeatureDataclass
    # todo: this class is a motivation for a none_cascade feature-flag in case of transformation errors
    pass


class HeadSeriesFeatureDataclass(metaclass=HeadSeriesFeatureDataclassMeta):
    pass


def get_feature(cls: FeatureDataclassMeta, name: str) -> Feature:
    """
    This free function can be used to determine the unit of a feature.
    """
    for f in cls.features:
        if f.name == name:
            return f
    else:
        raise KeyError(f"Dataclass {cls} does not have the feature {Feature}.")


def get_nested_keys(cls: NestSeriesFeatureDataclassMeta) -> Set[str]:
    keys = set()
    for field in cls.features:
        field_type = get_nested_type(field.type) if has_nested_type(field.type) else field.type
        if issubclass(field_type, SeriesDataclassIdent):
            continue
        elif isinstance(field_type, NestSeriesFeatureDataclass):
            keys = keys | get_nested_keys(field_type)
        elif field.input_key is not None:
            keys = keys | set(dict(field.input_key).keys())

    return keys


def is_feature_dataclass_meta(t: Type) -> bool:
    return isinstance(get_nested_type(t) if has_nested_type(t) else t, FeatureDataclassMeta)


def is_series_dataclass(t: Type) -> bool:
    return isinstance(get_nested_type(t) if has_nested_type(t) else t, NestSeriesFeatureDataclassMeta)


def is_nested_dataclass(t: Type, data_class: FeatureDataclassMeta) -> bool:
    nested_type = get_nested_type(t) if has_nested_type(t) else t
    is_class = inspect.isclass(nested_type)
    return issubclass(nested_type, data_class) if is_class else False


# todo: remove special cases below and use the more general upper one
def is_series_dataclass_ident(t: Type) -> bool:
    return is_nested_dataclass(t, SeriesDataclassIdent)


def is_nest_series_feature_dataclass(t: Type) -> bool:
    return is_nested_dataclass(t, NestSeriesFeatureDataclass)


def is_feature_dataclass(t: Type) -> bool:
    return is_nested_dataclass(t, FeatureDataclass)


def is_unique_common_feature_dataclass(t: Type) -> bool:
    return is_nested_dataclass(t, UniqueCommonFeatureDataclass)


def is_head_series_feature_dataclass(t: Type) -> bool:
    return is_nested_dataclass(t, HeadSeriesFeatureDataclass)


def get_nested_dataclass(t: Type, data_class: FeatureDataclassMeta) -> Optional[FeatureDataclassMeta]:
    nested_type = get_nested_type(t) if has_nested_type(t) else t
    return nested_type if issubclass(nested_type, data_class) else None


def get_head_series_feature_dataclass(t: Type) -> Optional[FeatureDataclassMeta]:
    return get_nested_dataclass(t, HeadSeriesFeatureDataclass)


def get_nest_series_feature_dataclass(t: Type) -> Optional[FeatureDataclassMeta]:
    return get_nested_dataclass(t, NestSeriesFeatureDataclass)
