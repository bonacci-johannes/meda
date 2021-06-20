import datetime
from typing import Mapping, Any, Type, Union, get_args, get_origin

__all__ = [
    "is_tuple", "is_frozen_set", "is_optional", "is_interval", "is_date", "is_datetime", "is_bool", "is_optional_bool",
    "is_optional_blob", "is_blob", "is_optional_numeric", "is_numeric", "is_mapping_str_to_any", "is_optional_date",
    "is_optional_datetime", "is_optional_interval", "has_nested_type", "get_nested_type", "get_nested_optionals"
]


def is_optional(t) -> bool:
    return get_origin(t) is Union and len(get_args(t)) == 2 and type(None) in get_args(t)


def is_tuple(t) -> bool:
    return get_origin(t) is tuple


def is_frozen_set(t) -> bool:
    return get_origin(t) is frozenset


def is_mapping_str_to_any(t) -> bool:
    """this check applies for our json datatype implementation"""
    return t is Mapping[str, Any]


def has_nested_type(t) -> bool:
    return is_tuple(t) or is_optional(t) or is_frozen_set(t)


def get_nested_type(t) -> Type:
    return get_args(t)[0]


def get_nested_optionals(t) -> Type:
    return get_nested_type(t) if is_optional(t) else t


def is_numeric(t) -> bool:
    return t in {int, float}


def is_blob(t) -> bool:
    return t in {str, bytes}


def is_bool(t) -> bool:
    return t is bool


def is_interval(t) -> bool:
    return t is datetime.timedelta


def is_date(t) -> bool:
    return t is datetime.date


def is_datetime(t) -> bool:
    return t is datetime.datetime


def is_optional_numeric(t) -> bool:
    return is_optional(t) and get_nested_type(t) in {int, float}


def is_optional_blob(t) -> bool:
    return is_optional(t) and get_nested_type(t) in {str, bytes}


def is_optional_bool(t) -> bool:
    return is_optional(t) and get_nested_type(t) is bool


def is_optional_interval(t) -> bool:
    return is_optional(t) and get_nested_type(t) is datetime.timedelta


def is_optional_date(t) -> bool:
    return is_optional(t) and get_nested_type(t) is datetime.date


def is_optional_datetime(t) -> bool:
    return is_optional(t) and get_nested_type(t) is datetime.datetime
