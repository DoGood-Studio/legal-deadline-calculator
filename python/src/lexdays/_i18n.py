"""Message rendering shared with the TypeScript package via data/i18n/messages.json."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Any

from . import _data

DEFAULT_LANG = "en"


def languages() -> tuple[str, ...]:
    return tuple(_data.messages()["languages"])


def pick(text: Mapping[str, str] | str | None, lang: str) -> str:
    """Choose ``lang`` from a ``{lang: text}`` mapping, falling back to English."""
    if text is None:
        return ""
    if isinstance(text, str):
        return text
    return text.get(lang) or text.get(DEFAULT_LANG) or next(iter(text.values()), "")


def format_date(day: date, lang: str) -> str:
    table = _data.messages()
    pattern = pick(table["date_format"], lang)
    weekday = pick({k: v[day.isoweekday() - 1] for k, v in table["weekdays"].items()}, lang)
    return pattern.format(
        iso=day.isoformat(),
        yyyy=f"{day.year:04d}",
        mm=f"{day.month:02d}",
        dd=f"{day.day:02d}",
        weekday=weekday,
    )


def _value(value: Any, lang: str) -> str:
    if isinstance(value, date):
        return format_date(value, lang)
    if isinstance(value, Mapping):
        return pick(value, lang)
    return str(value)


def render(key: str, params: Mapping[str, Any], override: Mapping[str, str] | None = None) -> dict[str, str]:
    """Render message ``key`` in every supported language."""
    templates = override or _data.messages()["messages"][key]
    out: dict[str, str] = {}
    for lang in languages():
        template = pick(templates, lang)
        out[lang] = template.format(**{name: _value(v, lang) for name, v in params.items()})
    return out
