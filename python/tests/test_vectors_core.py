"""Runs the shared engine conformance vectors (vectors/core/*.json)."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import pytest

import lexdays
import lexdays._i18n
from lexdays import Calendar, RulePack

from .conftest import load_vectors

CAL_VECTORS = load_vectors("core/calendar.json")
DL_VECTORS = load_vectors("core/deadline.json")
ERRORS = {
    "CoverageError": lexdays.CoverageError,
    "DataError": lexdays.DataError,
    "OptionError": lexdays.OptionError,
    "ValueError": ValueError,
    "TypeError": TypeError,
}


def _calendars() -> dict[str, Calendar]:
    built: dict[str, Calendar] = {}
    for cid, spec in CAL_VECTORS["calendars"].items():
        parent = built[spec["extends"]] if "extends" in spec else None
        built[cid] = Calendar(spec, parent=parent)
    return built


CALENDARS = _calendars()


def _holiday_rows(holidays: list[lexdays.Holiday]) -> list[list[str]]:
    rows = []
    for h in holidays:
        row = [h.date.isoformat(), h.id]
        if h.observed_from:
            row.append(h.observed_from.isoformat())
        rows.append(row)
    return rows


def _run_calendar_case(case: dict[str, Any]) -> Any:
    if case["fn"] == "load":
        return Calendar(case["spec"])
    cal = CALENDARS[case["calendar"]]
    args = dict(case["args"])
    fn = case["fn"]
    if fn == "holidays":
        return _holiday_rows(cal.holidays(args.pop("year"), **args))
    if fn == "holiday_ids":
        return [h.id for h in cal.holidays(args["year"])]
    if fn in ("is_business_day", "next_business_day", "previous_business_day"):
        result = getattr(cal, fn)(args.pop("date"), **args)
        return result.isoformat() if isinstance(result, date) else result
    if fn == "add_business_days":
        return cal.add_business_days(args.pop("date"), args.pop("n"), **args).isoformat()
    if fn == "business_days_between":
        return cal.business_days_between(args.pop("start"), args.pop("end"), **args)
    raise AssertionError(f"unknown fn {fn}")


@pytest.mark.parametrize("case", CAL_VECTORS["cases"], ids=lambda c: c["id"])
def test_calendar_vector(case: dict[str, Any]) -> None:
    if "error" in case:
        with pytest.raises(ERRORS[case["error"]]):
            _run_calendar_case(case)
    else:
        assert _run_calendar_case(case) == case["expect"]


def _pack(case: dict[str, Any]) -> RulePack:
    spec = case.get("pack_spec") or DL_VECTORS["rulepacks"][case["pack"]]
    override = CALENDARS.get(spec["calendar"]) if isinstance(spec, dict) and "calendar" in spec else None
    return RulePack(spec, calendar_override=override)


def _run_deadline_case(case: dict[str, Any]) -> lexdays.DeadlineResult:
    pack = _pack(case)
    return pack.compute(
        case["trigger"],
        case["period"],
        direction=case.get("direction", "after"),
        options=case.get("options"),
    )


@pytest.mark.parametrize("case", DL_VECTORS["cases"], ids=lambda c: c["id"])
def test_deadline_vector(case: dict[str, Any]) -> None:
    if "error" in case:
        with pytest.raises(ERRORS[case["error"]]):
            _run_deadline_case(case)
        return
    result = _run_deadline_case(case)
    expect = case["expect"]
    assert result.deadline.isoformat() == expect["deadline"]
    if "steps" in expect:
        assert [s.step for s in result.trace] == expect["steps"]
    if "changed" in expect:
        assert [s.changed for s in result.trace] == expect["changed"]
    if "ends_at" in expect:
        assert result.ends_at == expect["ends_at"]
    assert [n.code for n in result.notices] == expect.get("notices", [])
    # Every message must be fully rendered in every language.
    for step in result.trace:
        for lang in lexdays._i18n.languages():
            text = step.message[lang]
            assert text
            assert not re.search(r"\{\w+\}", text), text
    assert result.explain("tr")
    assert result.explain("en")
