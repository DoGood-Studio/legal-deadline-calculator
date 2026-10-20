"""Generates vectors/generated/differential.json: random cases computed by the Python package.

The TypeScript test-suite recomputes every case and must produce the same
deadline and a byte-identical result document (compared through its SHA-256),
including every rendered message in every language.

    uv run --project python python scripts/gen_differential.py
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import lexdays

SEED = 20261019
N_DEADLINES = 1200
N_CALENDAR = 600
ACT_CASES = 6  # random triggers per named act
OUT = Path(__file__).resolve().parents[1] / "vectors" / "generated" / "differential.json"


def canonical_hash(document: Any) -> str:
    text = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def random_date(rng: random.Random, cal: lexdays.Calendar) -> date:
    lo, hi = cal.coverage or (2000, 2030)
    first, last = date(lo, 1, 1), cal.coverage_until or date(hi, 12, 31)
    return first + timedelta(days=rng.randrange((last - first).days + 1))


def random_period(rng: random.Random) -> str:
    unit, top = rng.choice([("D", 120), ("W", 12), ("M", 8), ("Y", 2), ("bd", 30)])
    n = rng.randint(1, top)
    return f"{n}bd" if unit == "bd" else f"P{n}{unit}"


def calendar_choices(pack: lexdays.RulePack) -> list[str | None]:
    if pack.calendar_family is None:
        return [None]
    family = pack.calendar_family
    return [None, *[c for c in lexdays.list_calendars() if c == family or c.startswith(family + "-")]]


def main() -> None:
    rng = random.Random(SEED)
    packs = [lexdays.rulepack(p) for p in lexdays.list_rulepacks()]
    deadlines = []
    while len(deadlines) < N_DEADLINES:
        pack = rng.choice(packs)
        cal_id = rng.choice(calendar_choices(pack))
        cal = lexdays.calendar(cal_id) if cal_id else pack.calendar
        options = {name: rng.choice(spec["values"]) for name, spec in pack.options.items() if rng.random() < 0.6}
        case = {
            "pack": pack.id,
            "trigger": random_date(rng, cal).isoformat(),
            "period": random_period(rng),
            "direction": "before" if rng.random() < 0.15 else "after",
            "options": options,
        }
        if cal_id:
            case["calendar"] = cal_id
        try:
            result = lexdays.compute(
                case["pack"], case["trigger"], case["period"],
                direction=case["direction"], options=options, calendar=cal_id,
            )
        except lexdays.LexdaysError as exc:
            case["error"] = type(exc).__name__
        else:
            case["deadline"] = result.deadline.isoformat()
            case["sha256"] = canonical_hash({k: v for k, v in result.to_dict().items() if k != "version"})
        deadlines.append(case)

    # Named acts: each one with several random triggers (before and after any change of its period)
    # and random values for the options it does not imply.
    for pack in packs:
        for act in pack.acts.values():
            for _ in range(ACT_CASES):
                cal_id = rng.choice(calendar_choices(pack))
                cal = lexdays.calendar(cal_id) if cal_id else pack.calendar
                options = {
                    name: rng.choice(spec["values"]) for name, spec in pack.options.items()
                    if name not in act.options and rng.random() < 0.6
                }
                case = {"pack": pack.id, "trigger": random_date(rng, cal).isoformat(), "act": act.id, "options": options}
                if cal_id:
                    case["calendar"] = cal_id
                try:
                    result = lexdays.compute(case["pack"], case["trigger"], act=act.id, options=options, calendar=cal_id)
                except lexdays.LexdaysError as exc:
                    case["error"] = type(exc).__name__
                else:
                    case["deadline"] = result.deadline.isoformat()
                    case["sha256"] = canonical_hash({k: v for k, v in result.to_dict().items() if k != "version"})
                deadlines.append(case)

    calendar_cases = []
    calendars = lexdays.list_calendars()
    while len(calendar_cases) < N_CALENDAR:
        cal = lexdays.calendar(rng.choice(calendars))
        start = random_date(rng, cal)
        fn = rng.choice(["add_business_days", "business_days_between", "next_business_day", "previous_business_day"])
        case: dict[str, Any] = {"calendar": cal.id, "fn": fn, "date": start.isoformat()}
        try:
            if fn == "add_business_days":
                case["n"] = rng.randint(-60, 60)
                case["expect"] = cal.add_business_days(start, case["n"]).isoformat()
            elif fn == "business_days_between":
                end = start + timedelta(days=rng.randint(-120, 120))
                case["end"] = end.isoformat()
                case["expect"] = cal.business_days_between(start, end)
            else:
                case["expect"] = getattr(cal, fn)(start).isoformat()
        except lexdays.LexdaysError as exc:
            case.pop("expect", None)
            case["error"] = type(exc).__name__
        calendar_cases.append(case)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    document = {
        "description": "Generated by scripts/gen_differential.py from the Python package. Do not edit by hand; "
                       "regenerate after changing the engine or data. The TypeScript suite must reproduce it.",
        "seed": SEED,
        "deadlines": deadlines,
        "calendar": calendar_cases,
    }
    with OUT.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(document, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
    errors = sum(1 for c in deadlines if "error" in c)
    print(f"wrote {OUT.name}: {len(deadlines)} deadlines ({errors} expected errors), {len(calendar_cases)} calendar cases")


if __name__ == "__main__":
    main()
