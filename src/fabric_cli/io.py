from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_mapping(path: Path, description: str | None = None) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        label = description or path.name
        raise ValueError(f"{label} must contain a mapping")
    return value
