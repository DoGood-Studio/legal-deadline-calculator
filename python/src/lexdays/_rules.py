"""Legal deadline computation driven by rule packs (rules as data).

A rule pack is a JSON document that lists the steps a jurisdiction applies to
compute a deadline (count the period, extend it over a judicial recess, roll a
non-working last day forward, ...). Every step can cite the provision it comes
from, and every executed step is recorded in an explanation trace.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, TypeAlias

from . import _data, _dates, _i18n
from ._calendar import Calendar, Holiday, _check_keys, _check_name
from ._calendar import calendar as _load_calendar
from .errors import DataError, OptionError

UNITS = ("day", "week", "month", "year", "business_day")
DIRECTIONS = ("after", "before")

_ISO_PERIOD = re.compile(r"^P(\d+)([DWMY])$", re.IGNORECASE)
_SHORT_PERIOD = re.compile(r"^(\d+)\s*(bd|d|w|m|y)$", re.IGNORECASE)
_WORD_PERIOD = re.compile(
    r"^(\d+)\s*(business[ _-]?days?|working[ _-]?days?|days?|weeks?|months?|years?"
    r"|iş günü|gün|hafta|ay|yıl)$",
    re.IGNORECASE,
)
_UNIT_ALIASES = {
    "d": "day", "w": "week", "m": "month", "y": "year", "bd": "business_day",
    "day": "day", "days": "day", "week": "week", "weeks": "week",
    "month": "month", "months": "month", "year": "year", "years": "year",
    "gün": "day", "hafta": "week", "ay": "month", "yıl": "year", "iş günü": "business_day",
}
_TIME = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
_MONTH_DAY = re.compile(r"^(\d{2})-(\d{2})$")
_MAX_AMOUNT = 100_000

_PACK_KEYS = {
    "$schema", "id", "name", "description", "jurisdiction", "calendar", "calendar_family", "status",
    "non_working", "options", "steps", "citations", "sources", "disclaimer", "notes",
}
_COMMON_STEP_KEYS = {"type", "when", "cite", "message", "messages", "note"}
_STEP_KEYS = {
    "shift_trigger": {"days"},
    "count": {"exclude_start_day", "clear_days", "business_days"},
    "recess": {"name", "periods", "mode", "extension_days", "count_from"},
    "roll": {"direction", "half_days", "kinds", "weekend"},
    "add_days": {"days"},
    "ends_at": {"time"},
    "notice": {"code", "text"},
}
_CONDITION_KEYS = {
    "option", "equals", "in", "unit", "unit_in", "min_amount", "max_amount",
    "direction", "trigger_from", "trigger_before", "trigger_within", "date_within", "day_has",
    "non_working_day", "applied", "all", "any", "not",
}


# ------------------------------------------------------------------- results


@dataclass(frozen=True)
class Period:
    """A legal period such as 2 weeks or 10 working days."""

    amount: int
    unit: str

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError(f"period amount must be an int, got {type(self.amount).__name__}")
        if not 1 <= self.amount <= _MAX_AMOUNT:
            raise ValueError(f"period amount must be between 1 and {_MAX_AMOUNT}, got {self.amount}")
        if self.unit not in UNITS:
            raise ValueError(f"period unit must be one of {UNITS}, got {self.unit!r}")

    @classmethod
    def parse(cls, value: Any) -> Period:
        """Accepts ``Period``, ``"P2W"``, ``"10d"``, ``"5bd"``, ``"2 weeks"``, ``(2, "week")``
        or ``{"amount": 2, "unit": "week"}``."""
        if isinstance(value, Period):
            return value
        if isinstance(value, Mapping):
            return cls(value.get("amount"), value.get("unit"))  # type: ignore[arg-type]
        if isinstance(value, tuple) and len(value) == 2:
            return cls(value[0], value[1])
        if isinstance(value, str):
            text = value.strip()
            match = _ISO_PERIOD.match(text)
            if match:
                return cls(int(match.group(1)), _UNIT_ALIASES[match.group(2).lower()])
            match = _SHORT_PERIOD.match(text) or _WORD_PERIOD.match(text)
            if match:
                unit = match.group(2).lower().replace("-", " ").replace("_", " ")
                if unit.startswith(("business", "working")):
                    unit = "bd"
                if unit not in _UNIT_ALIASES:
                    raise ValueError(f"cannot parse period {value!r}; try 'P10D', '2w', '1m' or '5bd'")
                return cls(int(match.group(1)), _UNIT_ALIASES[unit])
            raise ValueError(f"cannot parse period {value!r}; try 'P10D', '2w', '1m' or '5bd'")
        raise TypeError(f"cannot use {type(value).__name__} as a period")

    def __str__(self) -> str:
        if self.unit == "business_day":
            return f"{self.amount}bd"
        return f"P{self.amount}{self.unit[0].upper()}"

    def to_dict(self) -> dict[str, Any]:
        return {"amount": self.amount, "unit": self.unit}


@dataclass(frozen=True)
class Citation:
    """The legal source a step relies on."""

    id: str
    label: Mapping[str, str] = field(hash=False, compare=False)
    url: str | None = None
    quote: Mapping[str, str] | None = field(default=None, hash=False, compare=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": dict(self.label),
            "url": self.url,
            "quote": dict(self.quote) if self.quote else None,
        }


@dataclass(frozen=True)
class TraceStep:
    """One executed step of a deadline computation."""

    step: str
    before: date
    after: date
    message: Mapping[str, str] = field(hash=False, compare=False)
    citation: Citation | None = None

    @property
    def changed(self) -> bool:
        return self.before != self.after

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "before": self.before.isoformat(),
            "after": self.after.isoformat(),
            "changed": self.changed,
            "message": dict(self.message),
            "citation": self.citation.to_dict() if self.citation else None,
        }


@dataclass(frozen=True)
class Notice:
    """A caveat attached to a result, e.g. a point on which case law is divided."""

    code: str
    message: Mapping[str, str] = field(hash=False, compare=False)
    citation: Citation | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": dict(self.message),
            "citation": self.citation.to_dict() if self.citation else None,
        }


@dataclass(frozen=True)
class DeadlineResult:
    """The computed deadline together with the reasoning that produced it."""

    deadline: date
    trigger: date
    period: Period
    direction: str
    rulepack: str
    calendar: str
    options: Mapping[str, Any] = field(hash=False, compare=False)
    trace: tuple[TraceStep, ...] = ()
    notices: tuple[Notice, ...] = ()
    ends_at: str | None = None
    timezone: str | None = None

    def explain(self, lang: str = "en") -> str:
        """Human-readable, numbered explanation in ``lang`` (``"en"`` or ``"tr"``)."""
        lines = []
        for number, step in enumerate(self.trace, start=1):
            line = f"{number}. {_i18n.pick(step.message, lang)}"
            if step.citation:
                line += f" [{_i18n.pick(step.citation.label, lang)}]"
            lines.append(line)
        lines.append(_i18n.render("explain.deadline", {"date": self.deadline})[_lang(lang)])
        if self.ends_at:
            time = f"{self.ends_at} ({self.timezone})" if self.timezone else self.ends_at
            lines.append(_i18n.render("explain.ends_at", {"time": time})[_lang(lang)])
        for notice in self.notices:
            text = _i18n.pick(notice.message, lang)
            lines.append(_i18n.render("explain.warning", {"text": text})[_lang(lang)])
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deadline": self.deadline.isoformat(),
            "ends_at": self.ends_at,
            "timezone": self.timezone,
            "trigger": self.trigger.isoformat(),
            "period": self.period.to_dict(),
            "direction": self.direction,
            "rulepack": self.rulepack,
            "calendar": self.calendar,
            "options": dict(self.options),
            "trace": [s.to_dict() for s in self.trace],
            "notices": [n.to_dict() for n in self.notices],
        }


def _lang(lang: str) -> str:
    return lang if lang in _i18n.languages() else _i18n.DEFAULT_LANG


# ------------------------------------------------------------------- engine


@dataclass
class _Context:
    trigger: date
    period: Period
    direction: str
    options: Mapping[str, Any]
    trace: list[TraceStep] = field(default_factory=list)
    notices: list[Notice] = field(default_factory=list)
    calendar: Calendar | None = None
    ends_at: str | None = None
    count_start: date | None = None

    @property
    def cal(self) -> Calendar:
        assert self.calendar is not None
        return self.calendar


Steps = list[Mapping[str, Any]]


class RulePack:
    """A jurisdiction's deadline rules, loaded from a JSON rule pack."""

    def __init__(self, spec: Mapping[str, Any], *, calendar_override: Calendar | None = None) -> None:
        spec = _check_keys(spec, _PACK_KEYS, "rule pack")
        pack_id = spec.get("id")
        if not isinstance(pack_id, str) or not pack_id:
            raise DataError("rule pack: 'id' must be a non-empty string")
        self._where = f"rule pack {pack_id!r}"
        self.id: str = pack_id
        self.name: Mapping[str, str] = _check_name(spec.get("name"), self._where)
        self.jurisdiction: str | None = spec.get("jurisdiction")
        self.status: str = spec.get("status", "experimental")
        self.description: Mapping[str, str] | None = spec.get("description")
        self.disclaimer: Mapping[str, str] | None = spec.get("disclaimer")
        self.sources: tuple[Any, ...] = tuple(spec.get("sources", ()))
        if calendar_override is not None:
            self.calendar = calendar_override
        elif "calendar" in spec:
            self.calendar = _load_calendar(spec["calendar"])
        else:
            raise DataError(f"{self._where}: 'calendar' is required")
        family = spec.get("calendar_family")
        if family is not None and not isinstance(family, str):
            raise DataError(f"{self._where}: 'calendar_family' must be a string")
        self.calendar_family: str | None = family
        self.citations: dict[str, Citation] = self._load_citations(spec.get("citations", {}))
        self.options: dict[str, Mapping[str, Any]] = self._load_options(spec.get("options", {}))
        self.non_working: Mapping[str, Any] = self._load_non_working(spec.get("non_working", {}))
        self.steps: Steps = self._load_steps(spec.get("steps"))

    def __repr__(self) -> str:
        return f"RulePack({self.id!r})"

    # ----------------------------------------------------------- validation

    def _load_citations(self, raw: Any) -> dict[str, Citation]:
        if not isinstance(raw, Mapping):
            raise DataError(f"{self._where}: 'citations' must be an object")
        out = {}
        for cid, raw_item in raw.items():
            item = _check_keys(raw_item, {"label", "url", "quote"}, f"{self._where}.citations[{cid}]")
            out[cid] = Citation(
                id=cid,
                label=_check_name(item.get("label"), f"{self._where}.citations[{cid}].label"),
                url=item.get("url"),
                quote=item.get("quote"),
            )
        return out

    def _load_options(self, raw: Any) -> dict[str, Mapping[str, Any]]:
        if not isinstance(raw, Mapping):
            raise DataError(f"{self._where}: 'options' must be an object")
        out = {}
        for name, raw_item in raw.items():
            here = f"{self._where}.options[{name}]"
            item = _check_keys(raw_item, {"values", "default", "description"}, here)
            values = item.get("values")
            if not isinstance(values, list) or not values:
                raise DataError(f"{here}.values must be a non-empty list")
            if item.get("default") not in values:
                raise DataError(f"{here}.default must be one of its values")
            out[name] = item
        return out

    def _resolve(self, value: Any, ctx: _Context | None, where: str) -> Any:
        """Resolve ``{"$option": name}`` references (validated when ctx is None)."""
        if isinstance(value, Mapping) and set(value) == {"$option"}:
            name = value["$option"]
            if name not in self.options:
                raise DataError(f"{where}: references unknown option {name!r}")
            return ctx.options[name] if ctx else self.options[name]["default"]
        return value

    def _load_non_working(self, raw: Any) -> Mapping[str, Any]:
        raw = _check_keys(raw, {"weekend", "kinds", "half_days"}, f"{self._where}.non_working")
        merged = {"weekend": True, "kinds": ["public"], "half_days": "working", **raw}
        self._check_non_working(merged, f"{self._where}.non_working")
        return merged

    def _check_non_working(self, conf: Mapping[str, Any], where: str) -> None:
        for key in ("weekend", "kinds", "half_days"):
            if key not in conf:
                continue
            value = self._resolve(conf[key], None, f"{where}.{key}")
            if key == "weekend" and not isinstance(value, bool):
                raise DataError(f"{where}.weekend must be true or false")
            if key == "kinds" and (not isinstance(value, list) or not all(isinstance(k, str) for k in value)):
                raise DataError(f"{where}.kinds must be a list of strings")
            if key == "half_days" and value not in ("working", "non_working"):
                raise DataError(f"{where}.half_days must be 'working' or 'non_working'")

    def _check_condition(self, cond: Any, where: str) -> None:
        cond = _check_keys(cond, _CONDITION_KEYS, where)
        if not cond:
            raise DataError(f"{where}: empty condition")
        if "option" in cond:
            name = cond["option"]
            if name not in self.options:
                raise DataError(f"{where}: unknown option {name!r}")
            if ("equals" in cond) == ("in" in cond):
                raise DataError(f"{where}: an option condition needs exactly one of 'equals' or 'in'")
            allowed = self.options[name]["values"]
            tested = [cond["equals"]] if "equals" in cond else cond["in"]
            if not isinstance(tested, list) or any(v not in allowed for v in tested):
                raise DataError(f"{where}: tests values that option {name!r} can never take")
        elif "equals" in cond or "in" in cond:
            raise DataError(f"{where}: 'equals'/'in' require 'option'")
        if "unit" in cond and cond["unit"] not in UNITS:
            raise DataError(f"{where}: unknown unit {cond['unit']!r}")
        if "unit_in" in cond and (
            not isinstance(cond["unit_in"], list) or any(u not in UNITS for u in cond["unit_in"])
        ):
            raise DataError(f"{where}: 'unit_in' must list valid units")
        for key in ("min_amount", "max_amount"):
            if key in cond and (isinstance(cond[key], bool) or not isinstance(cond[key], int)):
                raise DataError(f"{where}: {key} must be an integer")
        if "direction" in cond and cond["direction"] not in DIRECTIONS:
            raise DataError(f"{where}: direction must be one of {DIRECTIONS}")
        for key in ("trigger_from", "trigger_before"):
            if key in cond:
                _dates.parse_date(cond[key], field=f"{where}.{key}")
        for key in ("trigger_within", "date_within"):
            if key not in cond:
                continue
            windows = cond[key]
            if not isinstance(windows, list) or not windows:
                raise DataError(f"{where}.{key} must be a non-empty list of windows")
            for i, window in enumerate(windows):
                _check_keys(window, {"start", "end"}, f"{where}.{key}[{i}]")
                for part in ("start", "end"):
                    _month_day(window.get(part), f"{where}.{key}[{i}].{part}")
        if "day_has" in cond and not isinstance(cond["day_has"], str):
            raise DataError(f"{where}.day_has must be 'half_day' or a holiday kind")
        if "non_working_day" in cond and not isinstance(cond["non_working_day"], bool):
            raise DataError(f"{where}.non_working_day must be true or false")
        if "applied" in cond and cond["applied"] not in _STEP_KEYS:
            raise DataError(f"{where}.applied must be a step type")
        for key in ("all", "any"):
            if key in cond:
                if not isinstance(cond[key], list) or not cond[key]:
                    raise DataError(f"{where}.{key} must be a non-empty list")
                for i, sub in enumerate(cond[key]):
                    self._check_condition(sub, f"{where}.{key}[{i}]")
        if "not" in cond:
            self._check_condition(cond["not"], f"{where}.not")

    def _load_steps(self, raw: Any) -> Steps:
        if not isinstance(raw, list) or not raw:
            raise DataError(f"{self._where}: 'steps' must be a non-empty list")
        seen_count = False
        for index, step in enumerate(raw):
            stype = step.get("type") if isinstance(step, Mapping) else None
            here = f"{self._where}.steps[{index}]"
            if stype not in _STEP_KEYS:
                raise DataError(f"{here}: type must be one of {sorted(_STEP_KEYS)}")
            _check_keys(step, _COMMON_STEP_KEYS | _STEP_KEYS[stype], f"{here} ({stype})")
            if "when" in step:
                self._check_condition(step["when"], f"{here}.when")
            if "cite" in step and step["cite"] not in self.citations:
                raise DataError(f"{here}: cites unknown citation {step['cite']!r}")
            if "message" in step:
                _check_name(step["message"], f"{here}.message")
            if "messages" in step:
                if not isinstance(step["messages"], Mapping) or not step["messages"]:
                    raise DataError(f"{here}.messages must map message keys to {{lang: text}} objects")
                for key, text in step["messages"].items():
                    _check_name(text, f"{here}.messages[{key}]")
            if stype == "count":
                seen_count = True
                for key in ("exclude_start_day", "clear_days", "business_days"):
                    if key in step and not isinstance(self._resolve(step[key], None, here), bool):
                        raise DataError(f"{here}.{key} must be true or false")
            elif stype == "shift_trigger":
                if seen_count:
                    raise DataError(f"{here}: shift_trigger must come before the count step")
                _int_param(self._resolve(step.get("days"), None, here), f"{here}.days", -366, 366)
            elif stype == "add_days":
                _int_param(self._resolve(step.get("days"), None, here), f"{here}.days", -366, 366)
            elif stype == "recess":
                self._check_recess(step, here)
                if step.get("mode") == "defer_start" and seen_count:
                    raise DataError(f"{here}: a 'defer_start' recess must come before the count step")
            elif stype == "roll":
                direction = step.get("direction", "auto")
                if direction not in ("auto", "forward", "backward"):
                    raise DataError(f"{here}.direction must be auto, forward or backward")
                self._check_non_working(step, here)
            elif stype == "ends_at":
                time = self._resolve(step.get("time"), None, here)
                if not isinstance(time, str) or not _TIME.match(time):
                    raise DataError(f"{here}.time must be HH:MM")
            elif stype == "notice":
                if not isinstance(step.get("code"), str):
                    raise DataError(f"{here}.code must be a string")
                _check_name(step.get("text"), f"{here}.text")
        if not seen_count:
            raise DataError(f"{self._where}: needs at least one 'count' step")
        return list(raw)

    def _check_recess(self, step: Mapping[str, Any], here: str) -> None:
        _check_name(step.get("name"), f"{here}.name")
        if step.get("mode", "extend") not in ("extend", "suspend", "defer_start"):
            raise DataError(f"{here}.mode must be 'extend', 'suspend' or 'defer_start'")
        if step.get("mode", "extend") == "extend":
            _int_param(step.get("extension_days"), f"{here}.extension_days", 0, 366)
            count_from = self._resolve(step.get("count_from", "end"), None, here)
            if count_from not in ("end", "day_after_end"):
                raise DataError(f"{here}.count_from must be 'end' or 'day_after_end'")
        periods = step.get("periods")
        if not isinstance(periods, list) or not periods:
            raise DataError(f"{here}.periods must be a non-empty list")
        for i, period in enumerate(periods):
            _check_keys(period, {"start", "end", "since", "until"}, f"{here}.periods[{i}]")
            for key in ("start", "end"):
                _month_day(period.get(key), f"{here}.periods[{i}].{key}")

    def _option_values(self, options: Mapping[str, Any] | None) -> dict[str, Any]:
        options = dict(options or {})
        unknown = set(options) - set(self.options)
        if unknown:
            known = ", ".join(sorted(self.options)) or "none"
            raise OptionError(f"{self._where}: unknown option(s) {sorted(unknown)}; known: {known}")
        resolved = {}
        for name, spec in self.options.items():
            value = options.get(name, spec["default"])
            if value not in spec["values"]:
                allowed = spec["values"]
                raise OptionError(f"{self._where}: option {name!r} must be one of {allowed}, got {value!r}")
            resolved[name] = value
        return resolved

    # ------------------------------------------------------------- execution

    def compute(
        self,
        trigger: date | str,
        period: Period | str | Mapping[str, Any] | tuple[int, str],
        *,
        direction: str = "after",
        options: Mapping[str, Any] | None = None,
        calendar: str | Mapping[str, Any] | Calendar | None = None,
    ) -> DeadlineResult:
        """Compute the deadline for ``period`` counted from ``trigger``.

        ``direction="before"`` counts backwards (e.g. "at least 7 days before
        the hearing"). ``calendar`` selects the holiday calendar of the place
        that matters (e.g. the court's seat, ``"de-by"``) when the pack allows it.
        """
        start = _dates.parse_date(trigger, field="trigger")
        parsed = Period.parse(period)
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
        ctx = _Context(start, parsed, direction, self._option_values(options))
        ctx.calendar = self._calendar_for(calendar)
        current = start
        counted = False
        for step in self.steps:
            if "when" in step and not self._eval(step["when"], ctx, current):
                continue
            stype = step["type"]
            if stype == "count":
                if counted:
                    raise DataError(f"{self._where}: more than one count step matched {parsed}")
                counted = True
            current = getattr(self, f"_do_{stype}")(step, current, ctx)
        if not counted:
            raise DataError(f"{self._where}: no count step applies to {parsed} ({direction})")
        return DeadlineResult(
            deadline=current,
            trigger=start,
            period=parsed,
            direction=direction,
            rulepack=self.id,
            calendar=ctx.cal.id,
            options=ctx.options,
            trace=tuple(ctx.trace),
            notices=tuple(ctx.notices),
            ends_at=ctx.ends_at,
            timezone=ctx.cal.timezone,
        )

    def _calendar_for(self, override: str | Mapping[str, Any] | Calendar | None) -> Calendar:
        if override is None:
            return self.calendar
        chosen = _load_calendar(override)
        family = self.calendar_family
        if family is None:
            raise OptionError(f"{self._where} does not take a calendar override")
        if chosen.id != family and not chosen.id.startswith(family + "-"):
            raise OptionError(f"{self._where}: calendar must be {family!r} or {family}-*, got {chosen.id!r}")
        return chosen

    def _eval(self, cond: Mapping[str, Any], ctx: _Context, current: date) -> bool:
        if "option" in cond:
            value = ctx.options[cond["option"]]
            if "equals" in cond and value != cond["equals"]:
                return False
            if "in" in cond and value not in cond["in"]:
                return False
        if "unit" in cond and ctx.period.unit != cond["unit"]:
            return False
        if "unit_in" in cond and ctx.period.unit not in cond["unit_in"]:
            return False
        if "min_amount" in cond and ctx.period.amount < cond["min_amount"]:
            return False
        if "max_amount" in cond and ctx.period.amount > cond["max_amount"]:
            return False
        if "direction" in cond and ctx.direction != cond["direction"]:
            return False
        if "trigger_from" in cond and ctx.trigger < _dates.parse_date(cond["trigger_from"]):
            return False
        if "trigger_before" in cond and ctx.trigger >= _dates.parse_date(cond["trigger_before"]):
            return False
        # "trigger_within" tests the date counting starts from (e.g. the deemed date of service).
        served = ctx.count_start if ctx.count_start is not None else current
        if "trigger_within" in cond and not any(
            self._in_window(window, served) for window in cond["trigger_within"]
        ):
            return False
        if "date_within" in cond and not any(
            self._in_window(window, current) for window in cond["date_within"]
        ):
            return False
        if "day_has" in cond and not self._day_has(current, cond["day_has"], ctx):
            return False
        if "applied" in cond and not any(s.step == cond["applied"] and s.changed for s in ctx.trace):
            return False
        if "non_working_day" in cond:
            reason = ctx.cal.non_working_reason(current, **self._nw({}, ctx))
            if (reason is not None) != cond["non_working_day"]:
                return False
        if "all" in cond and not all(self._eval(c, ctx, current) for c in cond["all"]):
            return False
        if "any" in cond and not any(self._eval(c, ctx, current) for c in cond["any"]):
            return False
        return not ("not" in cond and self._eval(cond["not"], ctx, current))

    def _day_has(self, day: date, what: str, ctx: _Context) -> bool:
        if what == "half_day":
            kinds = self._resolve(self.non_working["kinds"], ctx, self._where)
            return any(h.is_half_day for h in ctx.cal.holidays_on(day, kinds=kinds))
        return any(h.kind == what for h in ctx.cal.holidays_on(day))

    def _in_window(self, window: Mapping[str, Any], day: date) -> bool:
        for year in (day.year - 1, day.year):
            span = self._recess_window(window, year)
            if span and span[0] <= day <= span[1]:
                return True
        return False

    def _nw(self, step: Mapping[str, Any], ctx: _Context) -> dict[str, Any]:
        conf = {**self.non_working, **{k: step[k] for k in ("weekend", "kinds", "half_days") if k in step}}
        return {k: self._resolve(v, ctx, self._where) for k, v in conf.items()}

    def _record(
        self, ctx: _Context, step: Mapping[str, Any], key: str, before: date, after: date,
        *, params: Mapping[str, Any],
    ) -> None:
        override = step.get("messages", {}).get(key) or step.get("message")
        message = _i18n.render(key, {"from": before, "to": after, **params}, override)
        citation = self.citations.get(step["cite"]) if "cite" in step else None
        ctx.trace.append(TraceStep(step["type"], before, after, message, citation))

    def _do_shift_trigger(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        days = self._resolve(step["days"], ctx, self._where)
        new = _dates.add_days(current, days)
        self._record(ctx, step, "shift_trigger", current, new, params={"days": days})
        return new

    def _do_count(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        ctx.count_start = current
        n, unit = ctx.period.amount, ctx.period.unit
        before = ctx.direction == "before"
        sign = -1 if before else 1
        suffix = ".before" if before else ""
        business_flag = bool(self._resolve(step.get("business_days", False), ctx, self._where))
        if unit == "business_day" or (business_flag and unit == "day"):
            conf = self._nw(step, ctx)
            clear = bool(self._resolve(step.get("clear_days", False), ctx, self._where))
            new = ctx.cal.add_business_days(current, sign * (n + int(clear)), **conf)
            key = "count.business_day" + suffix + (".clear" if clear else "")
        elif unit == "day":
            clear = bool(self._resolve(step.get("clear_days", False), ctx, self._where))
            exclude = bool(self._resolve(step.get("exclude_start_day", True), ctx, self._where))
            if clear:
                delta, key = n + 1, "count.day" + suffix + ".clear"
            elif exclude or before:
                delta, key = n, "count.day" + suffix
            else:
                delta, key = n - 1, "count.day.inclusive"
            new = _dates.add_days(current, sign * delta)
        elif unit == "week":
            new = _dates.add_days(current, sign * 7 * n)
            key = "count.week" + suffix
        else:
            months = n * (12 if unit == "year" else 1)
            new, clamped = _dates.add_months(current, sign * months)
            key = f"count.{unit}" + (".clamped" if clamped and not before else suffix)
        self._record(ctx, step, key, current, new, params={"n": n})
        return new

    def _recess_window(self, period: Mapping[str, Any], year: int) -> tuple[date, date] | None:
        if period.get("since") is not None and year < period["since"]:
            return None
        if period.get("until") is not None and year > period["until"]:
            return None
        sm, sd = _month_day(period["start"], "")
        em, ed = _month_day(period["end"], "")
        start = date(year, sm, sd)
        end_year = year + 1 if (em, ed) < (sm, sd) else year
        return start, date(end_year, em, ed)

    def _windows(self, step: Mapping[str, Any], lo: date, hi: date) -> list[tuple[date, date]]:
        found = []
        for year in range(lo.year - 1, hi.year + 1):
            for period in step["periods"]:
                window = self._recess_window(period, year)
                if window and window[1] >= lo and window[0] <= hi:
                    found.append(window)
        return sorted(set(found))

    def _do_recess(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        name = step["name"]
        if step.get("mode") == "defer_start":
            for start, end in self._windows(step, current, current):
                if start <= current <= end:
                    params = {"recess": name, "start": start, "end": end}
                    self._record(ctx, step, "recess.defer_start", current, end, params=params)
                    return end
            self._record(ctx, step, "recess.outside", current, current, params={"recess": name})
            return current
        if step.get("mode", "extend") == "extend":
            for start, end in self._windows(step, current, current):
                if start <= current <= end:
                    days = step["extension_days"]
                    count_from = self._resolve(step.get("count_from", "end"), ctx, self._where)
                    base = end if count_from == "end" else _dates.add_days(end, 1)
                    new = _dates.add_days(base, days)
                    key = "recess.extend" if count_from == "end" else "recess.extend.next_day"
                    params = {"recess": name, "start": start, "end": end, "days": days, "next": base}
                    self._record(ctx, step, key, current, new, params=params)
                    return new
            self._record(ctx, step, "recess.outside", current, current, params={"recess": name})
            return current
        # suspend: recess days inside the running period do not count, so the
        # end moves out by that many days (repeated until no new recess day
        # is swallowed by the extension).
        if ctx.direction == "before":
            raise DataError(f"{self._where}: recess mode 'suspend' does not support counting backwards")
        origin = ctx.count_start or ctx.trigger
        suspended = 0
        new = current
        while True:
            overlap = 0
            for start, end in self._windows(step, origin, new):
                first = max(start, origin + timedelta(days=1))
                last = min(end, new)
                overlap += max(0, (last - first).days + 1)
            if overlap == suspended:
                break
            suspended = overlap
            new = _dates.add_days(current, suspended)
        if suspended:
            params = {"recess": name, "days": suspended}
            self._record(ctx, step, "recess.suspend", current, new, params=params)
        else:
            self._record(ctx, step, "recess.outside", current, current, params={"recess": name})
        return new

    def _reason(self, why: Holiday | str) -> dict[str, str]:
        if why == "weekend":
            return _i18n.render("reason.weekend", {})
        assert isinstance(why, Holiday)
        if why.is_half_day:
            return _i18n.render("reason.half_day", {"holiday": why.name, "time": why.half_day_from})
        return {lang: why.label(lang) for lang in _i18n.languages()}

    def _do_roll(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        conf = self._nw(step, ctx)
        direction = step.get("direction", "auto")
        if direction == "auto":
            direction = "backward" if ctx.direction == "before" else "forward"
        why = ctx.cal.non_working_reason(current, **conf)
        if why is None:
            self._record(ctx, step, "roll.none", current, current, params={})
            return current
        if direction == "forward":
            new = ctx.cal.next_business_day(current, **conf)
        else:
            new = ctx.cal.previous_business_day(current, **conf)
        self._record(ctx, step, f"roll.{direction}", current, new, params={"reason": self._reason(why)})
        return new

    def _do_add_days(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        days = self._resolve(step["days"], ctx, self._where)
        new = _dates.add_days(current, days)
        self._record(ctx, step, "add_days", current, new, params={"days": days})
        return new

    def _do_ends_at(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        ctx.ends_at = self._resolve(step["time"], ctx, self._where)
        self._record(ctx, step, "ends_at", current, current, params={"time": ctx.ends_at})
        return current

    def _do_notice(self, step: Mapping[str, Any], current: date, ctx: _Context) -> date:
        citation = self.citations.get(step["cite"]) if "cite" in step else None
        ctx.notices.append(Notice(step["code"], step["text"], citation))
        return current


def _int_param(value: Any, where: str, lo: int, hi: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise DataError(f"{where}: expected an integer in [{lo}, {hi}], got {value!r}")
    return value


def _month_day(value: Any, where: str) -> tuple[int, int]:
    match = _MONTH_DAY.match(value) if isinstance(value, str) else None
    if not match:
        raise DataError(f"{where}: expected MM-DD, got {value!r}")
    month, day = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12 or not 1 <= day <= _dates.days_in_month(2001, month):
        raise DataError(f"{where}: {value!r} is not a valid month-day")
    return month, day


# ------------------------------------------------------------------ registry

_loaded: dict[str, RulePack] = {}

PackLike: TypeAlias = str | Mapping[str, Any] | RulePack


def rulepack(value: PackLike) -> RulePack:
    """Return a :class:`RulePack` from an id (e.g. ``"tr/hmk"``), a spec, or a pack."""
    if isinstance(value, RulePack):
        return value
    if isinstance(value, str):
        if value not in _loaded:
            _loaded[value] = RulePack(_data.load("rulepacks", value))
        return _loaded[value]
    if isinstance(value, Mapping):
        return RulePack(value)
    raise TypeError(f"expected a rule pack id, spec or RulePack, got {type(value).__name__}")


def compute(
    pack: PackLike,
    trigger: date | str,
    period: Period | str | Mapping[str, Any] | tuple[int, str],
    *,
    direction: str = "after",
    options: Mapping[str, Any] | None = None,
    calendar: str | Mapping[str, Any] | Calendar | None = None,
) -> DeadlineResult:
    """Compute a deadline: ``compute("tr/hmk", "2026-07-10", "P2W")``."""
    return rulepack(pack).compute(
        trigger, period, direction=direction, options=options, calendar=calendar
    )


def list_rulepacks() -> list[str]:
    """Ids of all bundled rule packs."""
    return _data.list_ids("rulepacks")
