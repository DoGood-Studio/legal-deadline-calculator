from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[2]
VECTORS = REPO / "vectors"


def load_vectors(name: str) -> dict[str, Any]:
    with (VECTORS / name).open(encoding="utf-8") as handle:
        data: dict[str, Any] = json.load(handle)
    return data


@pytest.fixture(scope="session")
def repo() -> Path:
    return REPO
