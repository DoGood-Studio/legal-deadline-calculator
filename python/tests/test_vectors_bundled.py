"""Runs the jurisdiction vectors (vectors/<jurisdiction>/*.json) against the bundled data."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import pytest

import lexdays
import lexdays._i18n

from .conftest import VECTORS, load_vectors

ERRORS = {
    "CoverageError": lexdays.CoverageError,
    "DataError": lexdays.DataError,
    "OptionError": lexdays.OptionError,
    "ValueError": ValueError,
}


def _collect(kind: str) -> list[dict[str, Any]]:
    cases = []
    for path in sorted(VECTORS.glob(f"*/{kind}.json")):
        if path.parent.name == "core":
            continue
        for case in load_vectors(f"{path.parent.name}/{kind}.json")["cases"]:
            cases.append({**case, "_file": path.parent.name})
    return cases


CAL_CASES = _collect("calendar")
DL_CASES = _collect("deadline")


def _rows(holidays: list[lexdays.Holiday]) -> list[list[str]]:
    return [[h.date.isoformat(), h.id] for h in holidays]


def _calendar_call(case: dict[str, Any]) -> Any:
    cal = lexdays.calendar(case["calendar"])
    args = dict(case["args"])
    fn = case["fn"]
    if fn == "holidays":
        return _rows(cal.holidays(args.pop("year"), **args))
    if fn == "holiday_ids":
        return [h.id for h in cal.holidays(args["year"])]
    if fn == "add_business_days":
        return cal.add_business_days(args.pop("date"), args.pop("n"), **args).isoformat()
    if fn == "business_days_between":
        return cal.business_days_between(args.pop("start"), args.pop("end"), **args)
    result = getattr(cal, fn)(args.pop("date"), **args)
    return result.isoformat() if isinstance(result, date) else result


@pytest.mark.parametrize("case", CAL_CASES, ids=lambda c: f"{c['_file']}:{c['id']}")
def test_bundled_calendar_vector(case: dict[str, Any]) -> None:
    if "error" in case:
        with pytest.raises(ERRORS[case["error"]]):
            _calendar_call(case)
        return
    result = _calendar_call(case)
    if "expect" in case:
        assert result == case["expect"]
    for item in case.get("expect_contains", []):
        assert item in result
    for item in case.get("expect_absent", []):
        assert item not in result


@pytest.mark.parametrize("case", DL_CASES, ids=lambda c: f"{c['_file']}:{c['id']}")
def test_bundled_deadline_vector(case: dict[str, Any]) -> None:
    run = lambda: lexdays.compute(  # noqa: E731
        case["pack"],
        case["trigger"],
        case["period"],
        direction=case.get("direction", "after"),
        options=case.get("options"),
        calendar=case.get("calendar"),
    )
    if "error" in case:
        with pytest.raises(ERRORS[case["error"]]):
            run()
        return
    result = run()
    expect = case["expect"]
    assert result.deadline.isoformat() == expect["deadline"], result.explain()
    if "steps" in expect:
        assert [s.step for s in result.trace] == expect["steps"]
    if "ends_at" in expect:
        assert result.ends_at == expect["ends_at"]
    if "notices" in expect:
        assert [n.code for n in result.notices] == expect["notices"]
    for step in result.trace:
        for lang in lexdays._i18n.languages():
            assert not re.search(r"\{\w+\}", step.message[lang])


def test_every_bundled_pack_and_calendar_loads() -> None:
    assert lexdays.list_calendars()
    for cid in lexdays.list_calendars():
        lexdays.calendar(cid)
    for pid in lexdays.list_rulepacks():
        pack = lexdays.rulepack(pid)
        assert pack.disclaimer, f"{pid} needs a disclaimer"
        assert all("cite" in s for s in pack.steps if s["type"] in ("count", "roll", "recess")), pid
