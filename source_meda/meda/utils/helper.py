import re


def camel_to_snake(string: str):
    string = re.sub(r'(?<!^)(?=[A-Z])', '_', string).lower()
    string = '_'.join( re.findall('(\d+|[A-Za-z]+)', string))
    string = re.sub('_+', '_', string)
    return string
