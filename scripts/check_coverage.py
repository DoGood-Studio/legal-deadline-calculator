"""Fail when a calendar's verified holiday data ends soon, so the next official list is added in time.

    uv run --project python python scripts/check_coverage.py [--months 6] [--today YYYY-MM-DD]

A calendar raises CoverageError past its coverage, so without this check a deadline tool quietly
starts failing for new deadlines (as eu-cj would have from late October 2026). CI runs it on every
push and on the weekly schedule.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

import lexdays


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--months", type=int, default=6, help="warning horizon in months (default 6)")
    parser.add_argument("--today", type=date.fromisoformat, default=date.today(), help="date to check from")
    args = parser.parse_args()
    horizon = args.today + timedelta(days=round(args.months * 30.44))
    short = []
    for cal_id in lexdays.list_calendars():
        cal = lexdays.calendar(cal_id)
        if cal.coverage is None:
            continue
        end = cal.coverage_until or date(cal.coverage[1], 12, 31)
        status = "ok" if end >= horizon else "ENDS SOON"
        print(f"{cal_id:<18} verified up to {end.isoformat()}  {status}")
        if end < horizon:
            short.append(cal_id)
    if short:
        print(
            f"\n{len(short)} calendar(s) end before {horizon.isoformat()}: {', '.join(short)}.\n"
            "Add the next official holiday list (and its source) and extend 'coverage'.",
            file=sys.stderr,
        )
        return 1
    print(f"\nAll calendars are verified past {horizon.isoformat()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
