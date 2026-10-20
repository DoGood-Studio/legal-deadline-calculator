"""Named acts: the objects and output around them. The computations themselves are conformance
vectors shared with the TypeScript engine (vectors/core/deadline.json, pack fx/acts)."""

from __future__ import annotations

from datetime import date

import pytest

import lexdays
from lexdays import Period, RulePack

from .test_vectors_core import CALENDARS, DL_VECTORS


def _acts_pack() -> RulePack:
    return RulePack(DL_VECTORS["rulepacks"]["fx/acts"], calendar_override=CALENDARS["fx"])


def test_act_carries_its_period_versions_and_citation() -> None:
    act = _acts_pack().act("appeal")
    assert act.rulepack == "fx/acts"
    assert act.period == Period(2, "week")
    assert act.direction == "after"
    assert act.group == "judgment"
    assert act.version_for("2024-03-11") == (Period(7, "day"), act.earlier[0].citation)
    assert act.version_for(date(2024, 3, 12)) == (Period(2, "week"), act.citation)
    data = act.to_dict()
    assert data["period"] == {"amount": 2, "unit": "week"}
    assert data["earlier"][0]["before"] == "2024-03-12"
    assert data["earlier"][0]["citation"]["id"] == "art_2_old"
    assert data["keywords"] == {"en": ["appeal"], "tr": ["kanun yolu"]}
    assert data["new"] is False
    assert _acts_pack().act("reply").to_dict()["new"] is True


def test_result_names_the_act_and_the_citation_in_force() -> None:
    pack = _acts_pack()
    old = pack.compute("2024-03-11", act="appeal")
    assert old.explain("tr").splitlines()[0] == "İstinaf (m.2 (2024 değişikliğinden önce))"
    assert old.to_dict()["act"]["citation"]["id"] == "art_2_old"
    assert old.to_dict()["act"]["label"]["en"] == "Appeal"
    plain = pack.compute("2024-03-11", "P7D")
    assert plain.act is None
    assert plain.to_dict()["act"] is None
    assert plain.explain("tr").splitlines()[0].startswith("1. ")
    assert old.deadline == plain.deadline


def test_unknown_act_names_the_known_ones() -> None:
    with pytest.raises(lexdays.NotFoundError, match="appeal, notice-before-hearing, reply"):
        _acts_pack().act("nope")
    with pytest.raises(LookupError):
        lexdays.rulepack("tr/hmk").act("nope")


def test_module_level_compute_takes_an_act() -> None:
    spec = dict(DL_VECTORS["rulepacks"]["fx/acts"], calendar="tr")
    assert lexdays.compute(spec, "2026-06-01", act="appeal").deadline == date(2026, 6, 15)
