"""Cross-checks the bundled calendars against independent sources.

    uv run --project python --with holidays python scripts/crosscheck_calendars.py [--govuk bank-holidays.json]

* every calendar except eu-cj is compared with python-holidays (vacanza/holidays);
* gb-eaw is also compared with the official GOV.UK bank holidays feed when given.

Only dates that fall on weekdays are compared, because the two sources record
weekend originals and substitute days differently. Known, documented
differences are listed in EXPECTED and reported separately.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date

import holidays

import lexdays

# (calendar, python-holidays country, subdivision, categories)
PAIRS = [
    ("tr", "TR", None, ("public", "half_day")),
    ("us", "US", None, ("public",)),
    ("us-ma", "US", "MA", ("public",)),
    ("gb-eaw", "GB", "ENG", ("public",)),
    ("de", "DE", None, ("public",)),
    *[(f"de-{s.lower()}", "DE", s, ("public",)) for s in
      ["BW", "BY", "BE", "BB", "HB", "HH", "HE", "MV", "NI", "NW", "RP", "SL", "SN", "ST", "SH", "TH"]],
    ("de-by-catholic", "DE", "BY", ("public", "catholic")),
]

# us-ma is "federal holidays + Massachusetts state holidays" (what Rule 6(a)(6) uses),
# whereas python-holidays US/MA models the state government's own holiday list.
STATE_ONLY = {"us-ma": ("MA", "Patriots")}


def weekday_dates(dates: set[date]) -> set[date]:
    return {d for d in dates if d.isoweekday() <= 5}


# Days that are not public holidays and that python-holidays does not model: administrative leave,
# executive-order closures, county-only observances and court-office closures.
NOT_COMPARED = {"administrative", "executive_closure", "suffolk", "court_closure"}


def ours(cal_id: str, year: int) -> set[date]:
    items = lexdays.calendar(cal_id).holidays(year)
    return weekday_dates({h.date for h in items if h.kind not in NOT_COMPARED})


def theirs(country: str, subdiv: str | None, cats: tuple[str, ...], year: int, cal_id: str = "") -> set[date]:
    if cal_id in STATE_ONLY:
        state, marker = STATE_ONLY[cal_id]
        federal = set(holidays.country_holidays(country, years=year).keys())
        state_days = {d for d, n in holidays.country_holidays(country, subdiv=state, years=year).items() if marker in n}
        return weekday_dates(federal | state_days)
    try:
        h = holidays.country_holidays(country, subdiv=subdiv, years=year, categories=cats)
    except (NotImplementedError, ValueError):
        h = holidays.country_holidays(country, subdiv=subdiv, years=year)
    return weekday_dates(set(h.keys()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--govuk", help="path to https://www.gov.uk/bank-holidays.json")
    args = parser.parse_args()
    problems = 0
    for cal_id, country, subdiv, cats in PAIRS:
        cal = lexdays.calendar(cal_id)
        lo, hi = cal.coverage or (1995, 2035)
        diffs = []
        for year in range(lo, hi + 1):
            a, b = ours(cal_id, year), theirs(country, subdiv, cats, year, cal_id)
            for d in sorted(a - b):
                diffs.append(f"  only lexdays : {d} {[h.id for h in cal.holidays_on(d)]}")
            for d in sorted(b - a):
                diffs.append(f"  only holidays: {d}")
        status = "OK" if not diffs else f"{len(diffs)} difference(s)"
        print(f"{cal_id:<16} vs python-holidays {country}/{subdiv or '-'} {lo}-{hi}: {status}")
        for line in diffs[:12]:
            print(line)
        problems += len(diffs)
    if args.govuk:
        with open(args.govuk, encoding="utf-8") as handle:
            feed = json.load(handle)["england-and-wales"]["events"]
        official = {date.fromisoformat(e["date"]) for e in feed}
        mine = set().union(*(ours("gb-eaw", y) for y in range(2019, 2029)))
        extra, missing = sorted(mine - official), sorted(official - mine)
        print(f"gb-eaw           vs GOV.UK feed 2019-2028: {'OK' if not (extra or missing) else 'DIFFERENT'}")
        for d in extra:
            print(f"  only lexdays : {d}")
        for d in missing:
            print(f"  only GOV.UK  : {d}")
        problems += len(extra) + len(missing)
    print(f"\nholidays {holidays.__version__}; total differences: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
