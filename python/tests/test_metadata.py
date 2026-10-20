"""Release metadata must agree everywhere it is written down.

A release bumps the version in several files by hand (see RELEASING.md). These tests catch a
file that was forgotten, including CITATION.cff, whose version and date GitHub and Zenodo show
to people who cite the project.
"""

from __future__ import annotations

import json
import re

import lexdays

from .conftest import REPO


def _field(text: str, pattern: str, where: str) -> str:
    match = re.search(pattern, text, re.MULTILINE)
    assert match, f"{where}: no match for {pattern!r}"
    return match.group(1)


def _citation(key: str) -> str:
    text = (REPO / "CITATION.cff").read_text(encoding="utf-8")
    return _field(text, rf"^{re.escape(key)}:\s*\"?([^\"\n]+?)\"?\s*$", "CITATION.cff")


def _latest_release() -> tuple[str, str]:
    text = (REPO / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(r"^## \[(\d+\.\d+\.\d+)\] - (\d{4}-\d{2}-\d{2})\s*$", text, re.MULTILINE)
    assert match, "CHANGELOG.md has no released section like '## [1.2.3] - 2026-01-31'"
    return match.group(1), match.group(2)


def test_version_is_the_same_everywhere() -> None:
    pyproject = (REPO / "python" / "pyproject.toml").read_text(encoding="utf-8")
    version_ts = (REPO / "js" / "src" / "version.ts").read_text(encoding="utf-8")
    versions = {
        "lexdays.__version__": lexdays.__version__,
        "python/pyproject.toml": _field(pyproject, r'^version\s*=\s*"([^"]+)"', "pyproject.toml"),
        "js/package.json": json.loads((REPO / "js" / "package.json").read_text(encoding="utf-8"))["version"],
        "js/src/version.ts": _field(version_ts, r'^export const VERSION = "([^"]+)";', "version.ts"),
        "CITATION.cff": _citation("version"),
    }
    assert len(set(versions.values())) == 1, versions


def test_citation_matches_the_latest_release() -> None:
    version, date = _latest_release()
    assert _citation("version") == version
    assert _citation("date-released") == date


def test_citation_license_matches_license_file() -> None:
    assert _citation("license") == "MIT"
    assert (REPO / "LICENSE").read_text(encoding="utf-8").startswith("MIT License")
