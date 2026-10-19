"""Command line interface: ``lexdays deadline tr/hmk 2026-07-10 P2W --lang tr``."""

from __future__ import annotations

import argparse
import contextlib
import json
import sys
from collections.abc import Sequence
from typing import Any

from . import __version__
from ._calendar import calendar, list_calendars
from ._i18n import format_date
from ._rules import compute, list_rulepacks, rulepack
from .errors import LexdaysError


def _option(text: str) -> tuple[str, Any]:
    if "=" not in text:
        raise argparse.ArgumentTypeError(f"options look like key=value, got {text!r}")
    key, raw = text.split("=", 1)
    value: Any = raw
    if raw.lower() in ("true", "false"):
        value = raw.lower() == "true"
    elif raw.lstrip("-").isdigit():
        value = int(raw)
    return key, value


def _print(data: Any, as_json: bool, text: str) -> None:
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(text)


def _cmd_deadline(args: argparse.Namespace) -> None:
    result = compute(
        args.pack,
        args.trigger,
        args.period,
        direction="before" if args.before else "after",
        options=dict(args.option or []),
    )
    _print(result.to_dict(), args.json, result.explain(args.lang))


def _cmd_holidays(args: argparse.Namespace) -> None:
    cal = calendar(args.calendar)
    items = cal.holidays(args.year, kinds=args.kind or "all")
    lines = []
    for h in items:
        extra = f"  [{h.kind}]" if h.kind != "public" else ""
        if h.half_day_from:
            extra += f"  (from {h.half_day_from})"
        lines.append(f"{format_date(h.date, args.lang)}  {h.label(args.lang)}{extra}")
    _print([h.to_dict() for h in items], args.json, "\n".join(lines))


def _cmd_add(args: argparse.Namespace) -> None:
    day = calendar(args.calendar).add_business_days(args.date, args.n)
    _print({"date": day.isoformat()}, args.json, format_date(day, args.lang))


def _cmd_between(args: argparse.Namespace) -> None:
    count = calendar(args.calendar).business_days_between(args.start, args.end)
    _print({"business_days": count}, args.json, str(count))


def _cmd_check(args: argparse.Namespace) -> None:
    cal = calendar(args.calendar)
    why = cal.non_working_reason(args.date)
    if why is None:
        label = "business day" if args.lang == "en" else "iş günü"
    elif why == "weekend":
        label = "weekend" if args.lang == "en" else "hafta sonu"
    else:
        label = why.label(args.lang)  # type: ignore[union-attr]
    _print({"business_day": why is None, "reason": label}, args.json, label)


def _cmd_list(args: argparse.Namespace) -> None:
    packs: list[dict[str, Any]] = []
    for pid in list_rulepacks():
        pack = rulepack(pid)
        packs.append({"id": pid, "name": dict(pack.name), "status": pack.status})
    calendars = list_calendars()
    data = {"calendars": calendars, "rulepacks": packs}
    text = "calendars: " + ", ".join(calendars) + "\nrule packs:\n" + "\n".join(
        f"  {p['id']:<12} {p['name'].get(args.lang) or p['name'].get('en')}  [{p['status']}]" for p in packs
    )
    _print(data, args.json, text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="lexdays", description="Explainable legal deadlines and business days."
    )
    parser.add_argument("--version", action="version", version=f"lexdays {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--lang", default="en", choices=["en", "tr"], help="output language")
    common.add_argument("--json", action="store_true", help="machine-readable output")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("deadline", parents=[common], help="compute a legal deadline")
    p.add_argument("pack", help="rule pack id, e.g. tr/hmk")
    p.add_argument("trigger", help="trigger date YYYY-MM-DD (e.g. date of service)")
    p.add_argument("period", help="period: P10D, 2w, 1m, 5bd ...")
    p.add_argument("--before", action="store_true", help="count backwards from the trigger")
    p.add_argument("-o", "--option", type=_option, action="append", metavar="KEY=VALUE")
    p.set_defaults(func=_cmd_deadline)

    p = sub.add_parser("holidays", parents=[common], help="list holidays of a year")
    p.add_argument("calendar")
    p.add_argument("year", type=int)
    p.add_argument("--kind", action="append", help="only these kinds (repeatable)")
    p.set_defaults(func=_cmd_holidays)

    p = sub.add_parser("add", parents=[common], help="add N business days to a date")
    p.add_argument("calendar")
    p.add_argument("date")
    p.add_argument("n", type=int)
    p.set_defaults(func=_cmd_add)

    p = sub.add_parser("between", parents=[common], help="count business days in (start, end]")
    p.add_argument("calendar")
    p.add_argument("start")
    p.add_argument("end")
    p.set_defaults(func=_cmd_between)

    p = sub.add_parser("check", parents=[common], help="is this date a business day?")
    p.add_argument("calendar")
    p.add_argument("date")
    p.set_defaults(func=_cmd_check)

    p = sub.add_parser("list", parents=[common], help="list bundled calendars and rule packs")
    p.set_defaults(func=_cmd_list)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # Never crash on a console that cannot print a character.
    with contextlib.suppress(AttributeError, ValueError):
        sys.stdout.reconfigure(errors="replace")  # type: ignore[union-attr]
    args = build_parser().parse_args(argv)
    try:
        args.func(args)
    except (LexdaysError, ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
