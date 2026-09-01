from datetime import datetime

import pytz


def get_current_datetime(settings):
    """
    Returns the current datetime localized to the timezone defined by settings.get_tz().
    Raises a TypeError if settings is None or invalid.
    """
    if settings is None:
        raise TypeError("settings must not be None")
    tzname = settings.get_tz()
    try:
        tz = pytz.timezone(tzname)
    except Exception:
        raise ValueError(f"invalid timezone '{tzname}'") from None

    return tz.localize(datetime.now())
