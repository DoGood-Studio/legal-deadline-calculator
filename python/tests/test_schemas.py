"""Every bundled data file must validate against the published JSON Schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from .conftest import REPO

DATA = REPO / "data"


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads((REPO / "spec" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


CALENDAR = _validator("calendar.schema.json")
RULEPACK = _validator("rulepack.schema.json")


def _files(kind: str) -> list[Path]:
    return sorted((DATA / kind).rglob("*.json"))


@pytest.mark.parametrize("path", _files("calendars"), ids=lambda p: p.stem)
def test_calendar_matches_schema(path: Path) -> None:
    errors = sorted(CALENDAR.iter_errors(json.loads(path.read_text(encoding="utf-8"))), key=str)
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors[:5])


@pytest.mark.parametrize(
    "path", _files("rulepacks"), ids=lambda p: p.relative_to(DATA / "rulepacks").as_posix()
)
def test_rulepack_matches_schema(path: Path) -> None:
    errors = sorted(RULEPACK.iter_errors(json.loads(path.read_text(encoding="utf-8"))), key=str)
    assert not errors, "\n".join(f"{list(e.absolute_path)}: {e.message}" for e in errors[:5])


def test_rulepack_ids_match_paths() -> None:
    for path in _files("rulepacks"):
        spec = json.loads(path.read_text(encoding="utf-8"))
        assert spec["id"] == path.relative_to(DATA / "rulepacks").with_suffix("").as_posix()


def test_calendar_ids_match_file_names() -> None:
    for path in _files("calendars"):
        assert json.loads(path.read_text(encoding="utf-8"))["id"] == path.stem
