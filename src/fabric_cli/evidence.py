from __future__ import annotations

from datetime import date, datetime
from typing import Any


def is_direct_evidence(value: Any) -> bool:
    if not isinstance(value, dict) or value.get("status") != "verified":
        return False
    source = value.get("source")
    return (
        isinstance(source, str) and bool(source.strip()) and _is_iso_date(value.get("observed_at"))
    )


def _is_iso_date(value: Any) -> bool:
    if isinstance(value, datetime):
        return True
    if isinstance(value, date):
        return True
    if not isinstance(value, str) or not value:
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return False
    return True
