"""Translations: every message exists in every language and keeps the same placeholders."""

from __future__ import annotations

import json
import re

import pytest

import lexdays

from .conftest import REPO

DATA = json.loads((REPO / "data" / "i18n" / "messages.json").read_text(encoding="utf-8"))
LANGS: list[str] = DATA["languages"]
PLACEHOLDER = re.compile(r"\{(\w+)\}")


@pytest.mark.parametrize("key", sorted(DATA["messages"]))
def test_message_has_every_language_with_the_same_placeholders(key: str) -> None:
    templates = DATA["messages"][key]
    assert set(templates) == set(LANGS), f"{key}: languages {sorted(set(LANGS) ^ set(templates))}"
    expected = set(PLACEHOLDER.findall(templates["en"]))
    for lang in LANGS:
        assert set(PLACEHOLDER.findall(templates[lang])) == expected, f"{key} [{lang}]"
        assert templates[lang].strip(), f"{key} [{lang}] is empty"


@pytest.mark.parametrize("lang", LANGS)
def test_date_format_and_weekdays(lang: str) -> None:
    fmt = DATA["date_format"][lang]
    assert set(PLACEHOLDER.findall(fmt)) <= {"iso", "yyyy", "mm", "dd", "weekday"}
    assert "{weekday}" in fmt
    names = DATA["weekdays"][lang]
    assert len(names) == 7
    assert len(set(names)) == 7


@pytest.mark.parametrize("lang", LANGS)
def test_explanations_render_in_every_language(lang: str) -> None:
    for pack, trigger, period, options in [
        ("tr/hmk", "2026-07-30", "P2W", {}),
        ("tr/iik", "2015-09-16", "P7D", {}),
        ("us/frcp", "2025-07-31", "P30D", {"service": "mail"}),
        ("gb-eaw/cpr", "2025-10-20", "P3D", {}),
    ]:
        direction = "before" if pack == "gb-eaw/cpr" else "after"
        text = lexdays.compute(pack, trigger, period, direction=direction, options=options).explain(lang)
        assert not PLACEHOLDER.search(text), text
        assert len(text.splitlines()) >= 2


def test_recess_names_are_translated() -> None:
    for pack_id in ("tr/hmk", "tr/cmk", "tr/iyuk"):
        for step in lexdays.rulepack(pack_id).steps:
            if step["type"] == "recess":
                assert set(step["name"]) >= set(LANGS), pack_id
