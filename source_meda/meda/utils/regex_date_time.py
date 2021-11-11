import re
from datetime import date, datetime, time


class RegexDateTime:
    # -----------------------------------------------------------------------------
    # Century boarder
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # dd.mm.yy will be mapped to dd.mm.19yy if yy>= boarder else dd.mm.20yy
    _cen_boarder = 40

    # -----------------------------------------------------------------------------
    # Regex Patterns
    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # ranges
    _re_year = "([1][9]|[2][0])[0-9][0-9]"
    _re_year_short = "[0-9][0-9]"
    _re_month = "([0-9]|[0][0-9]|1[0-2]|xx|XX|un|UN)"
    _re_day = "([0-9]|[0-2][0-9]|[3][0-1]|xx|XX|un|UN)"
    _re_hour = "([0-9]|0[0-9]|1[0-9]|2[0-3])"
    _re_min_sec = "[0-5][0-9]"

    # delimiters
    _re_delimiter_date = "[.-]"
    _re_delimiter_time = "[:]"
    _re_delimiter_datetime = "[tT_ ]"

    # joined patterns
    _re_invalid_date_short = _re_delimiter_date.join(['(0|00)', '(0|00)', '00'])
    _re_date_short_asc = _re_delimiter_date.join([_re_day, _re_month, _re_year_short])
    _re_date_desc = _re_delimiter_date.join([_re_year, _re_month, _re_day])
    _re_date_asc = _re_delimiter_date.join([_re_day, _re_month, _re_year])
    _re_time_hm = _re_delimiter_time.join([_re_hour, _re_min_sec])
    _re_time_hms = _re_delimiter_time.join([_re_hour, _re_min_sec, _re_min_sec])

    # +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    @classmethod
    def extract_date(cls, string: str) -> date:
        if re.fullmatch(cls._re_invalid_date_short, string):
            raise ValueError(f"Invalid date: {string}")
        elif re.fullmatch(cls._re_year, string):
            year = string
            day = month = '1'
        elif re.fullmatch(cls._re_date_short_asc, string):
            day, month, year = re.split(cls._re_delimiter_date, string)
            # century mapping
            year = int(year)
            if year < cls._cen_boarder:
                year += 2000
            else:
                year += 1900
        elif re.fullmatch(cls._re_date_asc, string):
            day, month, year = re.split(cls._re_delimiter_date, string)
        elif re.fullmatch(cls._re_date_desc, string):
            year, month, day = re.split(cls._re_delimiter_date, string)
        elif len(re.split(cls._re_delimiter_datetime, string)) == 2:
            # sometimes a datetime string is provided for a date
            # here we will drop the time
            date_str, time_str = re.split(cls._re_delimiter_datetime, string)
            year, month, day = re.split(cls._re_delimiter_date, date_str)
        else:
            raise ValueError(f"Unknown date format: {string}")

        # transform date to int
        day = int(day) if day.isdigit() else 1
        day = 1 if day == 0 else day

        month = int(month) if month.isdigit() else 1
        month = 1 if month == 0 else month

        year = int(year)

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
