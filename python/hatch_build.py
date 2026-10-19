"""Bundle the repository-level ``data/`` directory into the package.

From a git checkout the shared data lives one level up. An sdist already
contains it under ``src/lexdays/_data``, so building a wheel from the sdist
needs nothing extra.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        shared = Path(self.root).parent / "data"
        if not shared.is_dir():
            return
        target = "src/lexdays/_data" if self.target_name == "sdist" else "lexdays/_data"
        build_data["force_include"][str(shared)] = target
