"""Holiday calendars defined as data, plus business-day arithmetic."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, TypeAlias

from . import _data, _dates, _i18n
from .errors import CoverageError, DataError

DEFAULT_KINDS: tuple[str, ...] = ("public",)
HALF_DAY_POLICIES = ("working", "non_working")

_TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_KIND = re.compile(r"^[a-z][a-z_]*$")
_DIRECTIONS = ("on_or_after", "after", "on_or_before", "before")
_CALENDAR_KEYS = {
    "$schema", "id", "name", "description", "extends", "weekend", "timezone",
    "coverage", "sources", "holidays", "one_off", "remove", "notes",
}
_HOLIDAY_KEYS = {
    "id", "name", "kind", "rule", "since", "until", "except_years",
    "half_day", "observed", "source", "note",
}
_ONE_OFF_KEYS = {"id", "name", "date", "kind", "half_day", "source", "note"}
_RULE_KEYS = {
    "fixed": {"month", "day"},
    "nth_weekday": {"month", "weekday", "n"},
    "easter": {"offset", "method"},
    "dates": {"dates"},
    "weekday_relative": {"month", "day", "weekday", "direction"},
}
_Date: TypeAlias = date  # the Holiday.date field shadows the type inside the class

# Safety net: no real calendar has this many non-working days in a row.
_MAX_NON_WORKING_RUN = 1000


@dataclass(frozen=True)
class Holiday:
    """One holiday occurrence on a specific date."""

    date: date
    id: str
    name: Mapping[str, str] = field(hash=False, compare=False)
    kind: str = "public"
    half_day_from: str | None = None
    """``"13:00"`` when the day is non-working only from that time on."""
    observed_from: _Date | None = None
    """Original date, when this occurrence is an observed/substitute day."""
    source: str | None = field(default=None, hash=False, compare=False)

    @property
    def is_half_day(self) -> bool:
        return self.half_day_from is not None

    @property
    def is_observed(self) -> bool:
        return self.observed_from is not None

    def label(self, lang: str = "en") -> str:
        if self.observed_from is None:
            return _i18n.pick(self.name, lang)
        return _i18n.pick(_i18n.render("holiday.observed", {"name": self.name}), lang)

    def to_dict(self) -> dict[str, Any]:
        return {
            "date": self.date.isoformat(),
            "id": self.id,
            "name": dict(self.name),
            "kind": self.kind,
            "half_day_from": self.half_day_from,
            "observed_from": self.observed_from.isoformat() if self.observed_from else None,
        }


Kinds: TypeAlias = str | Iterable[str] | None


def _kinds(kinds: Kinds) -> frozenset[str]:
    if kinds is None:
        return frozenset(DEFAULT_KINDS)
    if isinstance(kinds, str):
        return frozenset((kinds,))
    return frozenset(kinds)


def _half(policy: str) -> str:
    if policy not in HALF_DAY_POLICIES:
        raise ValueError(f"half_days must be one of {HALF_DAY_POLICIES}, got {policy!r}")
    return policy


def _int(value: Any, where: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise DataError(f"{where}: expected an integer in [{lo}, {hi}], got {value!r}")
    return value


def _check_keys(obj: Any, allowed: set[str], where: str) -> Mapping[str, Any]:
    if not isinstance(obj, Mapping):
        raise DataError(f"{where}: expected an object")
    unknown = set(obj) - allowed
    if unknown:
        raise DataError(f"{where}: unknown field(s) {sorted(unknown)}")
    return obj


def _check_name(value: Any, where: str) -> Mapping[str, str]:
    if not isinstance(value, Mapping) or not value or not all(
        isinstance(k, str) and isinstance(v, str) and v for k, v in value.items()
    ):
        raise DataError(f"{where}: 'name' must be a non-empty {{lang: text}} object")
    return value


def _check_half_day(value: Any, where: str) -> str | None:
    if value is None:
        return None
    _check_keys(value, {"from"}, f"{where}.half_day")
    start = value.get("from")
    if not isinstance(start, str) or not _TIME.match(start):
        raise DataError(f"{where}.half_day.from: expected HH:MM, got {start!r}")
    return start


class Calendar:
    """A holiday calendar: weekend days plus holiday rules, all loaded from data.

    Use :func:`lexdays.calendar` to load a bundled one by id, or pass a spec
    dictionary to build your own.
    """

    def __init__(self, spec: Mapping[str, Any], *, parent: Calendar | None = None) -> None:
        spec = _check_keys(spec, _CALENDAR_KEYS, "calendar")
        cal_id = spec.get("id")
        if not isinstance(cal_id, str) or not cal_id:
            raise DataError("calendar: 'id' must be a non-empty string")
        where = f"calendar {cal_id!r}"
        self.id: str = cal_id
        self.name: Mapping[str, str] = (
            _check_name(spec["name"], where)
            if "name" in spec
            else (parent.name if parent else {"en": cal_id})
        )
        weekend = spec.get("weekend", sorted(parent.weekend) if parent else [6, 7])
        if not isinstance(weekend, list) or len(weekend) > 6:
            raise DataError(f"{where}: 'weekend' must be a list of at most 6 ISO weekdays")
        self.weekend: frozenset[int] = frozenset(_int(d, f"{where}.weekend", 1, 7) for d in weekend)
        self.timezone: str | None = spec.get("timezone", parent.timezone if parent else None)
        self.coverage: tuple[int, int] | None = self._coverage(spec, parent, where)
        self.sources: tuple[Any, ...] = tuple(spec.get("sources", ()))

        own = [self._check_holiday(h, where) for h in spec.get("holidays", ())]
        ids = [h["id"] for h in own]
        if len(ids) != len(set(ids)):
            raise DataError(f"{where}: duplicate holiday ids")
        remove = set(spec.get("remove", ()))
        inherited = [
            h for h in (parent._specs if parent else ()) if h["id"] not in remove and h["id"] not in ids
        ]
        self._specs: tuple[Mapping[str, Any], ...] = (*inherited, *own)
        self._one_off: tuple[Holiday, ...] = (
            *(parent._one_off if parent else ()),
            *(self._check_one_off(o, where) for o in spec.get("one_off", ())),
        )
        self._cache: dict[int, tuple[Holiday, ...]] = {}
        self._index: dict[int, dict[date, tuple[Holiday, ...]]] = {}

    def __repr__(self) -> str:
        return f"Calendar({self.id!r})"

    # ----------------------------------------------------------------- loading

    @staticmethod
    def _coverage(spec: Mapping[str, Any], parent: Calendar | None, where: str) -> tuple[int, int] | None:
        if "coverage" not in spec:
            return parent.coverage if parent else None
        cov = _check_keys(spec["coverage"], {"from", "to"}, f"{where}.coverage")
        lo = _int(cov.get("from"), f"{where}.coverage.from", _dates.MIN_YEAR + 1, _dates.MAX_YEAR - 1)
        hi = _int(cov.get("to"), f"{where}.coverage.to", lo, _dates.MAX_YEAR - 1)
        return (lo, hi)

    @staticmethod
    def _check_holiday(spec: Any, where: str) -> Mapping[str, Any]:
        spec = _check_keys(spec, _HOLIDAY_KEYS, f"{where}.holidays[]")
        hid = spec.get("id")
        if not isinstance(hid, str) or not hid:
            raise DataError(f"{where}: every holiday needs an 'id'")
        here = f"{where}.holidays[{hid}]"
        _check_name(spec.get("name"), here)
        kind = spec.get("kind", "public")
        if not isinstance(kind, str) or not _KIND.match(kind):
            raise DataError(f"{here}.kind: invalid kind {kind!r}")
        rule = spec.get("rule")
        if not isinstance(rule, Mapping) or rule.get("type") not in _RULE_KEYS:
            raise DataError(f"{here}.rule.type must be one of {sorted(_RULE_KEYS)}")
        rtype = rule["type"]
        _check_keys(rule, _RULE_KEYS[rtype] | {"type"}, f"{here}.rule")
        if rtype in ("fixed", "weekday_relative"):
            month = _int(rule.get("month"), f"{here}.rule.month", 1, 12)
            day = _int(rule.get("day"), f"{here}.rule.day", 1, 31)
            if day > _dates.days_in_month(2000, month):  # 2000 is a leap year
                raise DataError(f"{here}.rule: {month}/{day} never exists")
        if rtype in ("nth_weekday", "weekday_relative"):
            _int(rule.get("weekday"), f"{here}.rule.weekday", 1, 7)
        if rtype == "nth_weekday":
            _int(rule.get("month"), f"{here}.rule.month", 1, 12)
            n = _int(rule.get("n"), f"{here}.rule.n", -5, 5)
            if n == 0:
                raise DataError(f"{here}.rule.n must not be 0")
        if rtype == "weekday_relative" and rule.get("direction") not in _DIRECTIONS:
            raise DataError(f"{here}.rule.direction must be one of {_DIRECTIONS}")
        if rtype == "easter":
            _int(rule.get("offset", 0), f"{here}.rule.offset", -200, 200)
            if rule.get("method", "western") not in ("western", "orthodox"):
                raise DataError(f"{here}.rule.method must be 'western' or 'orthodox'")
        if rtype == "dates":
            values = rule.get("dates")
            if not isinstance(values, list) or not values:
                raise DataError(f"{here}.rule.dates must be a non-empty list")
            parsed = [_dates.parse_date(v, field=f"{here}.rule.dates") for v in values]
            if len(parsed) != len(set(parsed)):
                raise DataError(f"{here}.rule.dates contains duplicates")
            spec = {**spec, "_parsed": tuple(sorted(parsed))}
        for key in ("since", "until"):
            if key in spec and spec[key] is not None:
                _int(spec[key], f"{here}.{key}", _dates.MIN_YEAR, _dates.MAX_YEAR)
        for year in spec.get("except_years", ()):
            _int(year, f"{here}.except_years", _dates.MIN_YEAR, _dates.MAX_YEAR)
        checked: dict[str, Any] = {**spec, "_half": _check_half_day(spec.get("half_day"), here)}
        observed = checked.get("observed")
        if observed is not None:
            _check_keys(observed, {"shift", "avoid_collision", "kind"}, f"{here}.observed")
            obs_kind = observed.get("kind")
            kinds_given = (
                [obs_kind] if isinstance(obs_kind, str)
                else list(obs_kind.values()) if isinstance(obs_kind, Mapping)
                else [] if obs_kind is None else [None]
            )
            for value in kinds_given:
                if not isinstance(value, str) or not _KIND.match(value):
                    raise DataError(f"{here}.observed.kind must be a kind or a {{weekday: kind}} object")
            shift = observed.get("shift")
            if not isinstance(shift, Mapping) or not shift:
                raise DataError(f"{here}.observed.shift must map ISO weekdays to day offsets")
            for wd, offset in shift.items():
                _int(int(wd) if str(wd).isdigit() else -1, f"{here}.observed.shift key", 1, 7)
                _int(offset, f"{here}.observed.shift[{wd}]", -6, 6)
        return checked

    @staticmethod
    def _check_one_off(spec: Any, where: str) -> Holiday:
        spec = _check_keys(spec, _ONE_OFF_KEYS, f"{where}.one_off[]")
        oid = spec.get("id")
        if not isinstance(oid, str) or not oid:
            raise DataError(f"{where}: every one-off holiday needs an 'id'")
        here = f"{where}.one_off[{oid}]"
        kind = spec.get("kind", "public")
        if not isinstance(kind, str) or not _KIND.match(kind):
            raise DataError(f"{here}.kind: invalid kind {kind!r}")
        return Holiday(
            date=_dates.parse_date(spec.get("date"), field=f"{here}.date"),
            id=oid,
            name=_check_name(spec.get("name"), here),
            kind=kind,
            half_day_from=_check_half_day(spec.get("half_day"), here),
            source=spec.get("source"),
        )

    # ---------------------------------------------------------- holiday lists

    def _check_coverage(self, year: int) -> None:
        if self.coverage is not None and not self.coverage[0] <= year <= self.coverage[1]:
            lo, hi = self.coverage
            raise CoverageError(
                f"calendar {self.id!r} has verified holiday data for {lo}–{hi} only; "
                f"{year} is outside that range"
            )

    @staticmethod
    def _raw_dates(spec: Mapping[str, Any], year: int) -> list[date]:
        if spec.get("since") is not None and year < spec["since"]:
            return []
        if spec.get("until") is not None and year > spec["until"]:
            return []
        if year in spec.get("except_years", ()):
            return []
        rule = spec["rule"]
        rtype = rule["type"]
        if rtype == "fixed":
            if rule["day"] > _dates.days_in_month(year, rule["month"]):
                return []  # 29 February outside leap years
            return [date(year, rule["month"], rule["day"])]
        if rtype == "nth_weekday":
            found = _dates.nth_weekday(year, rule["month"], rule["weekday"], rule["n"])
            return [found] if found else []
        if rtype == "easter":
            base = (
                _dates.easter_orthodox(year)
                if rule.get("method") == "orthodox"
                else _dates.easter_western(year)
            )
            return [base + timedelta(days=rule.get("offset", 0))]
        if rtype == "dates":
            return [d for d in spec["_parsed"] if d.year == year]
        # weekday_relative
        if rule["day"] > _dates.days_in_month(year, rule["month"]):
            return []
        anchor = date(year, rule["month"], rule["day"])
        return [_dates.weekday_relative(anchor, rule["weekday"], rule["direction"])]

    def _year(self, year: int) -> tuple[Holiday, ...]:
        cached = self._cache.get(year)
        if cached is not None:
            return cached
        pairs: list[tuple[Holiday, Mapping[str, Any] | None]] = []
        # Neighbouring years are included because observed days can cross
        # 1 January (e.g. a Saturday New Year observed on 31 December).
        for y in (year - 1, year, year + 1):
            if not _dates.MIN_YEAR < y < _dates.MAX_YEAR:
                continue
            for spec in self._specs:
                for day in self._raw_dates(spec, y):
                    holiday = Holiday(
                        date=day,
                        id=spec["id"],
                        name=spec["name"],
                        kind=spec.get("kind", "public"),
                        half_day_from=spec["_half"],
                        source=spec.get("source"),
                    )
                    pairs.append((holiday, spec))
            pairs.extend((o, None) for o in self._one_off if o.date.year == y)
        pairs.sort(key=lambda p: (p[0].date, p[0].id))

        taken: dict[str, set[date]] = {}
        for holiday, _ in pairs:
            taken.setdefault(holiday.kind, set()).add(holiday.date)
        observed: list[Holiday] = []
        for holiday, holiday_spec in pairs:
            rule = holiday_spec.get("observed") if holiday_spec else None
            if not rule:
                continue
            offset = rule["shift"].get(str(holiday.date.isoweekday()))
            if not offset:
                continue
            target = holiday.date + timedelta(days=offset)
            if rule.get("avoid_collision"):
                step = 1 if offset > 0 else -1
                while target.isoweekday() in self.weekend or target in taken[holiday.kind]:
                    target += timedelta(days=step)
            taken[holiday.kind].add(target)
            obs_kind = rule.get("kind")
            if isinstance(obs_kind, Mapping):
                obs_kind = obs_kind.get(str(holiday.date.isoweekday()))
            observed.append(
                Holiday(
                    date=target,
                    id=holiday.id,
                    name=holiday.name,
                    kind=obs_kind or holiday.kind,
                    half_day_from=holiday.half_day_from,
                    observed_from=holiday.date,
                    source=holiday.source,
                )
            )
        result = tuple(
            sorted(
                (h for h in [*(p[0] for p in pairs), *observed] if h.date.year == year),
                key=lambda h: (h.date, h.observed_from is not None, h.id),
            )
        )
        self._cache[year] = result
        index: dict[date, list[Holiday]] = {}
        for h in result:
            index.setdefault(h.date, []).append(h)
        self._index[year] = {d: tuple(v) for d, v in index.items()}
        return result

    def holidays(self, year: int, *, kinds: Kinds = "all") -> list[Holiday]:
        """All holidays in ``year``. ``kinds="all"`` (default) includes every kind."""
        year = _int(year, "year", _dates.MIN_YEAR + 1, _dates.MAX_YEAR - 1)
        self._check_coverage(year)
        items = self._year(year)
        if kinds == "all":
            return list(items)
        wanted = _kinds(kinds)
        return [h for h in items if h.kind in wanted]

    def holidays_on(self, day: date | str, *, kinds: Kinds = "all") -> list[Holiday]:
        day = _dates.parse_date(day)
        self._check_coverage(day.year)
        self._year(day.year)
        items = self._index[day.year].get(day, ())
        if kinds == "all":
            return list(items)
        wanted = _kinds(kinds)
        return [h for h in items if h.kind in wanted]

    # ------------------------------------------------------------ business days

    def is_weekend(self, day: date | str) -> bool:
        return _dates.parse_date(day).isoweekday() in self.weekend

    def non_working_reason(
        self,
        day: date | str,
        *,
        kinds: Kinds = None,
        half_days: str = "working",
        weekend: bool = True,
    ) -> Holiday | str | None:
        """Why ``day`` is not a working day: a :class:`Holiday`, ``"weekend"``, or ``None``."""
        day = _dates.parse_date(day)
        policy = _half(half_days)
        for holiday in self.holidays_on(day, kinds=_kinds(kinds)):
            if not holiday.is_half_day or policy == "non_working":
                return holiday
        if weekend and day.isoweekday() in self.weekend:
            return "weekend"
        return None

    def is_business_day(
        self,
        day: date | str,
        *,
        kinds: Kinds = None,
        half_days: str = "working",
        weekend: bool = True,
    ) -> bool:
        """``True`` unless ``day`` is a weekend day or a holiday of one of ``kinds``.

        ``half_days="working"`` (default) treats half-day holidays such as the
        afternoon of an eve as working days.
        """
        return self.non_working_reason(day, kinds=kinds, half_days=half_days, weekend=weekend) is None

    def _step(self, day: date, direction: int, inclusive: bool, **opts: Any) -> date:
        current = day if inclusive else day + timedelta(days=direction)
        for _ in range(_MAX_NON_WORKING_RUN):
            if self.is_business_day(current, **opts):
                return current
            current += timedelta(days=direction)
        raise DataError(f"calendar {self.id!r}: no working day within {_MAX_NON_WORKING_RUN} days of {day}")

    def next_business_day(
        self, day: date | str, *, inclusive: bool = False, kinds: Kinds = None,
        half_days: str = "working", weekend: bool = True,
    ) -> date:
        """First working day after ``day`` (or on it, with ``inclusive=True``)."""
        return self._step(
            _dates.parse_date(day), 1, inclusive, kinds=kinds, half_days=half_days, weekend=weekend
        )

    def previous_business_day(
        self, day: date | str, *, inclusive: bool = False, kinds: Kinds = None,
        half_days: str = "working", weekend: bool = True,
    ) -> date:
        """Last working day before ``day`` (or on it, with ``inclusive=True``)."""
        return self._step(
            _dates.parse_date(day), -1, inclusive, kinds=kinds, half_days=half_days, weekend=weekend
        )

    def add_business_days(
        self, day: date | str, n: int, *, kinds: Kinds = None,
        half_days: str = "working", weekend: bool = True,
    ) -> date:
        """Move ``n`` working days from ``day`` (negative ``n`` moves backwards).

        The start day itself is never counted; ``n=0`` returns ``day`` unchanged.
        """
        current = _dates.parse_date(day)
        if isinstance(n, bool) or not isinstance(n, int):
            raise TypeError(f"n must be an int, got {type(n).__name__}")
        direction = 1 if n > 0 else -1
        for _ in range(abs(n)):
            current = self._step(
                current, direction, False, kinds=kinds, half_days=half_days, weekend=weekend
            )
        return current

    def business_days_between(
        self, start: date | str, end: date | str, *, kinds: Kinds = None,
        half_days: str = "working", weekend: bool = True,
    ) -> int:
        """Number of working days ``d`` with ``start < d <= end``.

        Negative when ``end`` is before ``start``, so that
        ``add_business_days(start, business_days_between(start, end))`` lands on
        ``end`` whenever ``end`` is itself a working day.
        """
        a, b = _dates.parse_date(start, field="start"), _dates.parse_date(end, field="end")
        sign = 1
        if b < a:
            a, b, sign = b, a, -1
        count = 0
        current = a + timedelta(days=1)
        while current <= b:
            if self.is_business_day(current, kinds=kinds, half_days=half_days, weekend=weekend):
                count += 1
            current += timedelta(days=1)
        return sign * count


# --------------------------------------------------------------------- registry

_loaded: dict[str, Calendar] = {}


def load_calendar(cal_id: str, _chain: tuple[str, ...] = ()) -> Calendar:
    """Load a bundled calendar by id (cached)."""
    if cal_id in _loaded:
        return _loaded[cal_id]
    if cal_id in _chain:
        raise DataError(f"calendar inheritance cycle: {' -> '.join((*_chain, cal_id))}")
    spec = _data.load("calendars", cal_id)
    parent_id = spec.get("extends")
    parent = load_calendar(parent_id, (*_chain, cal_id)) if parent_id else None
    cal = Calendar(spec, parent=parent)
    _loaded[cal_id] = cal
    return cal


def calendar(value: str | Mapping[str, Any] | Calendar) -> Calendar:
    """Return a :class:`Calendar` from an id, a spec dictionary, or a calendar."""
    if isinstance(value, Calendar):
        return value
    if isinstance(value, str):
        return load_calendar(value)
    if isinstance(value, Mapping):
        parent_id = value.get("extends")
        return Calendar(value, parent=load_calendar(parent_id) if parent_id else None)
    raise TypeError(f"expected a calendar id, spec or Calendar, got {type(value).__name__}")


def list_calendars() -> list[str]:
    """Ids of all bundled calendars."""
    return _data.list_ids("calendars")
