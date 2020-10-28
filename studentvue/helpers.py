import os
from datetime import datetime, timedelta


def base64ToFile(strBase64, fileName):
    import base64
    fileDecoded = base64.b64decode(strBase64)

    file = open(fileName, "wb")
    file.write(fileDecoded)
    file.close()

    return os.path.realpath(file.name)


def convert_to_timedelta(time_val):
    """
    Given a *time_val* (string) such as '5d', returns a timedelta object
    representing the given value (e.g. timedelta(days=5)).  Accepts the
    following '<num><char>' formats:

    =========   ======= ===================
    Character   Meaning Example
    =========   ======= ===================
    s           Seconds '60s' -> 60 Seconds
    m           Minutes '5m'  -> 5 Minutes
    h           Hours   '24h' -> 24 Hours
    d           Days    '7d'  -> 7 Days
    w           Weeks   '2w'  -> 2 Weeks
    =========   ======= ===================

    Examples::

        >>> convert_to_timedelta('3w')
        datetime.timedelta(21)
        >>> convert_to_timedelta('7d')
        datetime.timedelta(7)
        >>> convert_to_timedelta('24h')
        datetime.timedelta(1)
        >>> convert_to_timedelta('60m')
        datetime.timedelta(0, 3600)
        >>> convert_to_timedelta('120s')
        datetime.timedelta(0, 120)
    """
    num = int(time_val[:-1])
    if time_val.endswith('s'):
        return timedelta(seconds=num)
    elif time_val.endswith('m'):
        return timedelta(minutes=num)
    elif time_val.endswith('h'):
        return timedelta(hours=num)
    elif time_val.endswith('d'):
        return timedelta(days=num)
    elif time_val.endswith('w'):
        return timedelta(weeks=num)


def now_timedelta_to_date(time_val):
    return datetime.now() - convert_to_timedelta(time_val)


def convert_string_to_date(date):
    return datetime.strptime(date, '%m/%d/%Y')
