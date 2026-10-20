"""lexdays — explainable legal deadlines and business days.

>>> import lexdays
>>> cal = lexdays.calendar("us")
>>> cal.add_business_days("2026-07-02", 1).isoformat()
'2026-07-06'
"""

from __future__ import annotations

from ._calendar import Calendar, Holiday, calendar, list_calendars
from ._rules import (
    Citation,
    DeadlineResult,
    Notice,
    Period,
    RulePack,
    TraceStep,
    compute,
    list_rulepacks,
    rulepack,
)
from ._version import __version__
from .errors import (
    CoverageError,
    DataError,
    LexdaysError,
    NotFoundError,
    OptionError,
)

__all__ = [
    "Calendar",
    "Citation",
    "CoverageError",
    "DataError",
    "DeadlineResult",
    "Holiday",
    "LexdaysError",
    "NotFoundError",
    "Notice",
    "OptionError",
    "Period",
    "RulePack",
    "TraceStep",
    "__version__",
    "calendar",
    "compute",
    "list_calendars",
    "list_rulepacks",
    "rulepack",
]
