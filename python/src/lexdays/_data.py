"""Access to the bundled JSON data (calendars, rule packs, messages)."""

from __future__ import annotations

import json
import re
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

from .errors import NotFoundError

_ID = re.compile(r"^[a-z0-9]+(?:[-_/][a-z0-9]+)*$")


@lru_cache(maxsize=1)
def data_root() -> Path:
    """Directory holding the shared data.

    Installed wheels ship it as ``lexdays/_data``. When running from a source
    checkout the canonical ``data/`` directory at the repository root is used.
    """
    bundled = Path(__file__).parent / "_data"
    if bundled.is_dir():
        return bundled
    checkout = Path(__file__).resolve().parents[3] / "data"
    if checkout.is_dir():
        return checkout
    raise RuntimeError("lexdays data files are missing; reinstall the package")


@cache
def _read(path: Path) -> Any:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def load(kind: str, item_id: str) -> Any:
    """Load ``data/<kind>/<item_id>.json``; ids are validated to block path tricks."""
    if not isinstance(item_id, str) or not _ID.match(item_id):
        raise NotFoundError(f"invalid {kind[:-1]} id: {item_id!r}")
    path = data_root() / kind / f"{item_id}.json"
    if not path.is_file():
        raise NotFoundError(f"unknown {kind[:-1]}: {item_id!r} (see lexdays.list_{kind}())")
    return _read(path)


def list_ids(kind: str) -> list[str]:
    base = data_root() / kind
    if not base.is_dir():
        return []
    ids = (p.relative_to(base).with_suffix("").as_posix() for p in base.rglob("*.json"))
    return sorted(i for i in ids if not i.split("/")[-1].startswith("_"))


def messages() -> Any:
    return _read(data_root() / "i18n" / "messages.json")
