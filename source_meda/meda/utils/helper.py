import re


def camel_to_snake(string: str):
    return re.sub(r'(?<!^)(?=[A-Z,0-9])', '_', string).lower()
