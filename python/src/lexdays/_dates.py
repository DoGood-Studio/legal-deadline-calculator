"""Pure civil-date arithmetic on the proleptic Gregorian calendar.

Everything here works on :class:`datetime.date` only. There are no time zones,
no clocks and no locale settings involved, so results are deterministic on
every machine.
"""

from __future__ import annotations

import calendar as _stdcal
import re
from datetime import date, datetime, timedelta

_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

MIN_YEAR = 1
MAX_YEAR = 9999


def parse_date(value: object, *, field: str = "date") -> date:
    """Return ``value`` as a :class:`date`.

    Accepts a ``date`` or a strict ``YYYY-MM-DD`` string. A ``datetime`` is
    rejected on purpose: which calendar day a moment belongs to depends on a
    time zone, and guessing it silently is a classic source of off-by-one bugs.
    """
    if isinstance(value, datetime):
        raise TypeError(
            f"{field}: expected a date, got a datetime. Convert it with "
            ".date() in the time zone that matters for your deadline."
        )
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        match = _ISO_DATE.match(value)
        if not match:
            raise ValueError(f"{field}: expected YYYY-MM-DD, got {value!r}")
        year, month, day = (int(part) for part in match.groups())
        try:
            return date(year, month, day)
        except ValueError as exc:
            raise ValueError(f"{field}: {value!r} is not a valid date ({exc})") from None
    raise TypeError(f"{field}: expected a date or 'YYYY-MM-DD' string, got {type(value).__name__}")


def add_days(day: date, days: int) -> date:
    try:
        return day + timedelta(days=days)
    except OverflowError:
        raise ValueError(f"date out of range: {day.isoformat()} {days:+d} days") from None


def days_in_month(year: int, month: int) -> int:
    return _stdcal.monthrange(year, month)[1]


def add_months(day: date, months: int) -> tuple[date, bool]:
    """Add calendar months, keeping the day of month.

    When the target month is shorter (31 January + 1 month), the result is the
    last day of the target month. Returns ``(result, clamped)``.
    """
    index = day.year * 12 + (day.month - 1) + months
    year, month0 = divmod(index, 12)
    if not MIN_YEAR <= year <= MAX_YEAR:
        raise ValueError(f"date out of range: {day.isoformat()} {months:+d} months")
    month = month0 + 1
    last = days_in_month(year, month)
    if day.day > last:
        return date(year, month, last), True
    return date(year, month, day.day), False


def easter_western(year: int) -> date:
    """Gregorian Easter Sunday (anonymous Gregorian algorithm)."""
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7  # noqa: E741 - name from the published algorithm
    m = (a + 11 * h + 22 * l) // 451
    month, day = divmod(h + l - 7 * m + 114, 31)
    return date(year, month, day + 1)


def easter_orthodox(year: int) -> date:
    """Orthodox Easter Sunday expressed as a Gregorian date (Meeus' Julian algorithm)."""
    a = year % 4
    b = year % 7
    c = year % 19
    d = (19 * c + 15) % 30
    e = (2 * a + 4 * b - d + 34) % 7
    month, day = divmod(d + e + 114, 31)
    julian_offset = year // 100 - year // 400 - 2
    return date(year, month, day + 1) + timedelta(days=julian_offset)


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date | None:
    """The ``n``-th ISO ``weekday`` (1=Monday) of a month; negative ``n`` counts from the end.

    Returns ``None`` when the month has no such day (e.g. a fifth Monday).
    """
    if n == 0:
        raise ValueError("n must not be 0")
    last = days_in_month(year, month)
    if n > 0:
        first = date(year, month, 1)
        day = 1 + (weekday - first.isoweekday()) % 7 + 7 * (n - 1)
    else:
        end = date(year, month, last)
        day = last - (end.isoweekday() - weekday) % 7 - 7 * (-n - 1)
    if 1 <= day <= last:
        return date(year, month, day)
    return None


def weekday_relative(anchor: date, weekday: int, direction: str) -> date:
    """First ISO ``weekday`` on/after/before ``anchor``."""
    if direction == "on_or_after":
        return anchor + timedelta(days=(weekday - anchor.isoweekday()) % 7)
    if direction == "after":
        return weekday_relative(anchor + timedelta(days=1), weekday, "on_or_after")
    if direction == "on_or_before":
        return anchor - timedelta(days=(anchor.isoweekday() - weekday) % 7)
    if direction == "before":
        return weekday_relative(anchor - timedelta(days=1), weekday, "on_or_before")
    raise ValueError(f"unknown direction {direction!r}")
