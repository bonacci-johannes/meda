import re
from datetime import date, datetime, time


class RegexDateTime:
    # -----------------------------------------------------------------------------
    # Regex Patterns
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ranges
    _re_year = "([1][9]|[2][0])[0-9][0-9]"
    _re_month = "([1-9]|[0][1-9]|1[0-2])"
    _re_day = "([1-9]|[0-2][0-9]|[3][0-1])"
    _re_hour = "([0-9]|0[0-9]|1[0-9]|2[0-3])"
    _re_min_sec = "[0-5][0-9]"

    # delimiters
    _re_delimiter_date = "[.-]"
    _re_delimiter_time = "[:]"
    _re_delimiter_datetime = "[tT_ ]"

    # joined patterns
    _re_date_desc = _re_delimiter_date.join([_re_year, _re_month, _re_day])
    _re_date_asc = _re_delimiter_date.join([_re_day, _re_month, _re_year])
    _re_time_hm = _re_delimiter_time.join([_re_hour, _re_min_sec])
    _re_time_hms = _re_delimiter_time.join([_re_hour, _re_min_sec, _re_min_sec])

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @classmethod
    def extract_date(cls, string: str) -> date:
        if re.fullmatch(cls._re_year, string):
            year = int(string)
            day = month = 1
        elif re.fullmatch(cls._re_date_asc, string):
            day, month, year = [int(a) for a in re.split(cls._re_delimiter_date, string)]
        elif re.fullmatch(cls._re_date_desc, string):
            year, month, day = [int(a) for a in re.split(cls._re_delimiter_date, string)]
        elif len(re.split(cls._re_delimiter_datetime, string)) == 2:
            # sometimes a datetime string is provided for a date
            # here we will drop the time
            date_str, time_str = re.split(cls._re_delimiter_datetime, string)
            year, month, day = [int(a) for a in re.split(cls._re_delimiter_date, date_str)]
        else:
            raise ValueError(f"Unknown date format: {string}")

        return date(year=year, month=month, day=day)

    @classmethod
    def extract_time(cls, string: str) -> time:
        if re.fullmatch(cls._re_time_hms, string):
            hour, minute, second = [int(a) for a in re.split(cls._re_delimiter_time, string)]
        elif re.fullmatch(cls._re_time_hm, string):
            hour, minute = [int(a) for a in re.split(cls._re_delimiter_time, string)]
            second = 0
        else:
            raise ValueError(f"Unknown time format: {string}")

        return time(hour=hour, minute=minute, second=second)

    @classmethod
    def extract_datetime(cls, string) -> datetime:
        date_str, time_str = re.split(cls._re_delimiter_datetime, string)
        _date = cls.extract_date(date_str)
        _time = cls.extract_time(time_str)

        return datetime(year=_date.year, month=_date.month, day=_date.day,
                        hour=_time.hour, minute=_time.minute, second=_time.second)
