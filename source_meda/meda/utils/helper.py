import re
from typing import Union, Type


def camel_to_snake(string: str) -> str:
    string = re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()
    string = '_'.join(re.findall('(\d+|[A-Za-z]+)', string))
    string = re.sub('_+', '_', string)
    return string


def numeric_type_of_string(string: str) -> Union[Type[int], Type[float], Type[str]]:
    """
    This function determines the numeric type of string,
    for non-numeric strings the str type is returned
    """
    if string.isnumeric():
        return int
    try:
        _ = float(string)
        return float
    except (TypeError, ValueError):
        try:
            _ = float(string.replace(',', '.').replace('>', '').replace('<', ''))
            return float
        except (TypeError, ValueError):
            return str


def string_to_numeric(string: str) -> Union[int, float, str]:
    """ This function converts to numeric datatype if possible"""
    # replace comma by period
    # convert
    if string.isnumeric():
        return int(string)
    try:
        return float(string)
    except (TypeError, ValueError):
        try:
            return float(string.replace(',', '.').replace('>', '').replace('<', ''))
        except (TypeError, ValueError):
            return string
