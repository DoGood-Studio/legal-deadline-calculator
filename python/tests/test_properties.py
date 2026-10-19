"""Property-based tests: invariants that must hold for every input, checked with Hypothesis."""

from __future__ import annotations

from datetime import date, timedelta

from hypothesis import assume, given, settings
from hypothesis import strategies as st

import lexdays
from lexdays import Period
from lexdays._dates import add_months, parse_date

CALENDARS = ["tr", "us", "gb-eaw", "de-by-catholic", "eu-cj"]
# Packs whose final step rolls a non-working last day to a working day.
ROLLING_PACKS = ["tr/hmk", "tr/iik", "tr/cmk", "tr/iyuk", "tr/vuk", "tr/aym", "eu/cj", "de/zpo"]
ALL_PACKS = [*ROLLING_PACKS, "us/frcp", "gb-eaw/cpr"]


def _dates_in(cal_id: str) -> st.SearchStrategy[date]:
    lo, hi = lexdays.calendar(cal_id).coverage or (2000, 2030)
    margin = min(400, (hi - lo + 1) * 365 // 4)
    return st.dates(
        min_value=date(lo, 1, 1) + timedelta(days=margin),
        max_value=date(hi, 12, 31) - timedelta(days=margin),
    )


def _compute(pack_id: str, trigger: date, period: Period) -> lexdays.DeadlineResult:
    """Compute, discarding examples that run past a calendar's verified years."""
    try:
        return lexdays.compute(pack_id, trigger, period)
    except lexdays.CoverageError:
        assume(False)
        raise


calendar_and_date = st.sampled_from(CALENDARS).flatmap(lambda c: st.tuples(st.just(c), _dates_in(c)))
pack_and_date = st.sampled_from(ALL_PACKS).flatmap(
    lambda p: st.tuples(st.just(p), _dates_in(lexdays.rulepack(p).calendar.id))
)
periods = st.one_of(
    st.builds(Period, st.integers(1, 120), st.just("day")),
    st.builds(Period, st.integers(1, 12), st.just("week")),
    st.builds(Period, st.integers(1, 6), st.just("month")),
    st.builds(Period, st.integers(1, 2), st.just("year")),
    st.builds(Period, st.integers(1, 30), st.just("business_day")),
)


@settings(max_examples=400)
@given(calendar_and_date, st.integers(-40, 40))
def test_add_business_days_lands_on_a_business_day(cd: tuple[str, date], n: int) -> None:
    cal_id, day = cd
    cal = lexdays.calendar(cal_id)
    result = cal.add_business_days(day, n)
    if n == 0:
        assert result == day
        return
    assert cal.is_business_day(result)
    assert (result > day) if n > 0 else (result < day)
    assert cal.business_days_between(day, result) == n


@settings(max_examples=400)
@given(calendar_and_date, st.integers(0, 90))
def test_business_days_between_forward_and_backward_agree(cd: tuple[str, date], span: int) -> None:
    cal_id, day = cd
    cal = lexdays.calendar(cal_id)
    other = day + timedelta(days=span)
    forward = cal.business_days_between(day, other)
    backward = cal.business_days_between(other, day)
    # (a, b] and [a, b) differ only in their end points.
    assert forward + backward == int(cal.is_business_day(other)) - int(cal.is_business_day(day))
    assert 0 <= forward <= span


@settings(max_examples=400)
@given(calendar_and_date)
def test_next_business_day_skips_only_non_working_days(cd: tuple[str, date]) -> None:
    cal_id, day = cd
    cal = lexdays.calendar(cal_id)
    nxt = cal.next_business_day(day, inclusive=True)
    assert nxt >= day
    assert cal.is_business_day(nxt)
    current = day
    while current < nxt:
        assert not cal.is_business_day(current)
        current += timedelta(days=1)
    prev = cal.previous_business_day(day, inclusive=True)
    assert prev <= day
    assert cal.is_business_day(prev)


@settings(max_examples=600)
@given(pack_and_date, periods)
def test_deadline_trace_is_a_consistent_chain(pd: tuple[str, date], period: Period) -> None:
    pack_id, trigger = pd
    if pack_id == "gb-eaw/cpr" and period.unit == "business_day":
        return  # CPR periods are calendar periods
    result = _compute(pack_id, trigger, period)
    assert result.deadline >= trigger
    assert result.trace[0].before == trigger
    assert result.trace[-1].after == result.deadline
    for previous, step in zip(result.trace, result.trace[1:], strict=False):
        assert step.before == previous.after
    for step in result.trace:
        assert step.message["en"]
        assert step.message["tr"]
    assert result.explain("tr")
    assert result.to_dict()["deadline"] == result.deadline.isoformat()


@settings(max_examples=600)
@given(st.sampled_from(ROLLING_PACKS).flatmap(
    lambda p: st.tuples(st.just(p), _dates_in(lexdays.rulepack(p).calendar.id))), periods)
def test_rolling_packs_never_end_on_a_non_working_day(pd: tuple[str, date], period: Period) -> None:
    pack_id, trigger = pd
    pack = lexdays.rulepack(pack_id)
    result = _compute(pack_id, trigger, period)
    nw = pack.non_working
    half = nw["half_days"] if isinstance(nw["half_days"], str) else "working"
    assert pack.calendar.is_business_day(result.deadline, kinds=nw["kinds"], half_days=half)


@settings(max_examples=500)
@given(pack_and_date, periods)
def test_later_trigger_never_gives_an_earlier_deadline(pd: tuple[str, date], period: Period) -> None:
    """Monotonicity, except at the end of a judicial recess.

    There the law itself breaks it: under HMK 104 a 2-week period from 17
    August 2026 ends on 31 August, inside the recess, and is extended to
    8 September, while the same period from 18 August ends on 1 September.
    """
    pack_id, trigger = pd
    if pack_id == "gb-eaw/cpr" and period.unit == "business_day":
        return
    a = _compute(pack_id, trigger, period)
    b = _compute(pack_id, trigger + timedelta(days=1), period)
    extended = any(s.step == "recess" and s.changed for s in a.trace)
    if not extended:
        assert b.deadline >= a.deadline


@given(st.dates(min_value=date(10, 1, 1), max_value=date(9990, 12, 31)), st.integers(-60, 60))
def test_add_months_clamps_and_round_trips_day_numbers(day: date, months: int) -> None:
    result, clamped = add_months(day, months)
    assert (result.year * 12 + result.month) - (day.year * 12 + day.month) == months
    assert result.day == day.day or (clamped and result.day < day.day)


@given(st.dates(min_value=date(1, 1, 1), max_value=date(9999, 12, 31)))
def test_parse_date_round_trip(day: date) -> None:
    assert parse_date(day.isoformat()) == day


@given(periods)
def test_period_string_round_trip(period: Period) -> None:
    assert Period.parse(str(period)) == period
