import datetime as dt
from dateutil import parser
from dateutil.tz import UTC

def get_utc_datetime():
    return dt.datetime.now(UTC)

def utc_to_string(utc_datetime):
    return str(utc_datetime)

def utc_from_string(utc_datetime_string):
    return parser.parse(utc_datetime_string)
