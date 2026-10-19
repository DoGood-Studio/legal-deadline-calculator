"""Public API edge cases and input validation (Python-specific behaviour)."""

from __future__ import annotations

from datetime import date, datetime

import pytest

import lexdays
from lexdays import Period
from lexdays._dates import add_days, add_months, nth_weekday, parse_date, weekday_relative


def test_datetime_is_rejected_with_a_helpful_message() -> None:
    with pytest.raises(TypeError, match=r"\.date\(\)"):
        parse_date(datetime(2026, 1, 1, 12, 0))
    with pytest.raises(TypeError):
        parse_date(20260101)


def test_date_range_limits() -> None:
    with pytest.raises(ValueError, match="out of range"):
        add_days(date(9999, 12, 31), 1)
    with pytest.raises(ValueError, match="out of range"):
        add_months(date(1, 1, 31), -1)
    with pytest.raises(ValueError, match="must not be 0"):
        nth_weekday(2026, 1, 1, 0)
    with pytest.raises(ValueError, match="unknown direction"):
        weekday_relative(date(2026, 1, 1), 1, "sideways")
    assert nth_weekday(2026, 2, 1, 5) is None  # February 2026 has four Mondays


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("P10D", Period(10, "day")), ("p2w", Period(2, "week")), ("1m", Period(1, "month")),
        ("2 years", Period(2, "year")), ("5bd", Period(5, "business_day")),
        ("5 business days", Period(5, "business_day")), ("3 working-days", Period(3, "business_day")),
        ("10 gün", Period(10, "day")), ("2 hafta", Period(2, "week")), ("1 ay", Period(1, "month")),
        ("1 yıl", Period(1, "year")), ("5 iş günü", Period(5, "business_day")),
        ((3, "week"), Period(3, "week")), ({"amount": 4, "unit": "day"}, Period(4, "day")),
    ],
)
def test_period_parsing(value: object, expected: Period) -> None:
    assert Period.parse(value) == expected
    assert Period.parse(expected) is expected


@pytest.mark.parametrize("value", ["", "P", "10", "ten days", "P1H", "0d", "100001d", 3.5, None])
def test_period_parsing_rejects(value: object) -> None:
    with pytest.raises((ValueError, TypeError)):
        Period.parse(value)


def test_period_type_checks() -> None:
    with pytest.raises(TypeError):
        Period(True, "day")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unit must be one of"):
        Period(1, "hour")


def test_result_serialisation_and_explanation() -> None:
    result = lexdays.compute("tr/hmk", "2026-07-30", "P2W", options={"recess_extension_from": "end"})
    data = result.to_dict()
    assert data["deadline"] == "2026-09-07"
    assert data["timezone"] == "Europe/Istanbul"
    assert data["trace"][1]["citation"]["label"]["tr"] == "HMK m.102 ve m.104"
    method = next(n for n in data["notices"] if n["code"] == "recess-7-september-method")
    assert method["citation"]["id"] == "hgk_2017"
    text = result.explain("tr")
    assert "Bitiş saati: 23:59 (Europe/Istanbul)" in text
    assert "Not:" in text
    assert result.explain("xx").startswith("1.")  # unknown language falls back to English
    assert "Deadline: 2026-09-07 (Monday)" in result.explain("en")


def test_holiday_objects() -> None:
    cal = lexdays.calendar("us")
    observed = [h for h in cal.holidays(2026) if h.is_observed]
    assert observed[0].label("en") == "Independence Day (observed)"
    assert observed[0].to_dict()["observed_from"] == "2026-07-04"
    eve = lexdays.calendar("tr").holidays_on("2026-05-26")[0]
    assert eve.is_half_day
    assert eve.label("tr").startswith("Kurban Bayramı Arifesi")
    assert lexdays.calendar("tr").is_weekend("2026-05-23")
    assert repr(cal) == "Calendar('us')"
    assert repr(lexdays.rulepack("us/frcp")) == "RulePack('us/frcp')"


def test_calendar_and_pack_resolution() -> None:
    cal = lexdays.calendar("de-by")
    assert lexdays.calendar(cal) is cal
    spec = {"id": "mine", "extends": "de", "holidays": [
        {"id": "x", "name": {"en": "X"}, "rule": {"type": "fixed", "month": 6, "day": 1}}]}
    mine = lexdays.calendar(spec)
    assert [h.id for h in mine.holidays_on("2026-06-01")] == ["x"]
    with pytest.raises(TypeError):
        lexdays.calendar(42)  # type: ignore[arg-type]
    with pytest.raises(lexdays.NotFoundError):
        lexdays.calendar("../etc/passwd")
    with pytest.raises(lexdays.NotFoundError):
        lexdays.calendar("does-not-exist")
    pack = lexdays.rulepack("tr/hmk")
    assert lexdays.rulepack(pack) is pack
    with pytest.raises(TypeError):
        lexdays.rulepack(3.14)  # type: ignore[arg-type]


def test_calendar_override_rules() -> None:
    with pytest.raises(lexdays.OptionError, match="does not take a calendar override"):
        lexdays.compute("tr/hmk", "2026-07-30", "P2W", calendar="tr")
    with pytest.raises(lexdays.OptionError, match="calendar must be"):
        lexdays.compute("de/zpo", "2026-07-30", "P2W", calendar="tr")
    result = lexdays.compute("de/zpo", "2025-07-15", "P1M", calendar=lexdays.calendar("de-by-catholic"))
    assert result.calendar == "de-by-catholic"


def test_business_day_argument_checks() -> None:
    cal = lexdays.calendar("tr")
    with pytest.raises(TypeError):
        cal.add_business_days("2026-01-05", 1.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="half_days must be"):
        cal.is_business_day("2026-01-05", half_days="sometimes")
    with pytest.raises(lexdays.CoverageError):
        cal.holidays(1999)


def test_every_error_is_a_lexdays_error() -> None:
    for cls in (lexdays.DataError, lexdays.CoverageError, lexdays.OptionError, lexdays.NotFoundError):
        assert issubclass(cls, lexdays.LexdaysError)
