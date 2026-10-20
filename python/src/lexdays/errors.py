"""Exceptions raised by lexdays.

Every exception derives from :class:`LexdaysError` and from the closest
built-in type, so callers can catch either.
"""

from __future__ import annotations


class LexdaysError(Exception):
    """Base class for all lexdays errors."""


class DataError(LexdaysError, ValueError):
    """A calendar or rule pack definition is invalid."""


class CoverageError(LexdaysError, ValueError):
    """The requested year is outside the years a calendar has verified data for.

    lexdays refuses to guess: a missing religious or one-off holiday would
    silently produce a wrong deadline.
    """


class OptionError(LexdaysError, ValueError):
    """An option passed to a rule pack is unknown or has an invalid value."""


class NotFoundError(LexdaysError, LookupError):
    """No bundled calendar, rule pack or act has the requested id."""
