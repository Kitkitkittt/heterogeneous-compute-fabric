from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fabric_cli.safety import contains_private_identity

ADMISSION_SCHEMA = "heterogeneous-compute-fabric/admission-observations-v2"
MAX_ADMISSION_AGE = timedelta(hours=24)
MAX_CLOCK_SKEW = timedelta(minutes=5)
COLLECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._+-]*$")
PUBLIC_SOURCE_REF = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:issues|pull)/\d+(?:#.*)?$"
)


@dataclass(frozen=True)
class AdmissionProvenance:
    observed_at: datetime
    collector: str
    source_ref: str

    def as_dict(self) -> dict[str, str]:
        return {
            "collector": self.collector,
            "observed_at": self.observed_at.isoformat(),
            "source_ref": self.source_ref,
        }


def new_admission_provenance(collector: str, source_ref: str) -> AdmissionProvenance:
    return parse_admission_provenance(
        {
            "collector": collector,
            "observed_at": datetime.now(UTC).isoformat(),
            "source_ref": source_ref,
        }
    )


def parse_admission_provenance(
    value: dict[str, Any],
    *,
    now: datetime | None = None,
) -> AdmissionProvenance:
    observed_value = value.get("observed_at")
    collector = value.get("collector")
    source_ref = value.get("source_ref")
    if not isinstance(observed_value, str) or not observed_value:
        raise ValueError("admission provenance requires observed_at")
    try:
        observed_at = datetime.fromisoformat(observed_value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("admission observed_at must be an ISO-8601 timestamp") from exc
    if observed_at.tzinfo is None:
        raise ValueError("admission observed_at must include a UTC offset")
    observed_at = observed_at.astimezone(UTC)
    current = (now or datetime.now(UTC)).astimezone(UTC)
    if observed_at > current + MAX_CLOCK_SKEW:
        raise ValueError("admission observations are future-dated")
    if current - observed_at > MAX_ADMISSION_AGE:
        raise ValueError("admission observations are stale")
    if not isinstance(collector, str) or not COLLECTOR_ID.fullmatch(collector):
        raise ValueError("admission provenance requires a valid collector identity")
    if (
        not isinstance(source_ref, str)
        or not PUBLIC_SOURCE_REF.fullmatch(source_ref)
        or contains_private_identity(source_ref)
    ):
        raise ValueError("admission provenance requires a public-safe GitHub issue or PR source")
    return AdmissionProvenance(observed_at, collector, source_ref)


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
