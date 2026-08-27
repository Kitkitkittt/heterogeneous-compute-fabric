from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fabric_cli.safety import contains_private_identity

ADMISSION_SCHEMA = "heterogeneous-compute-fabric/admission-observations-v2"
MAX_ADMISSION_AGE = timedelta(hours=24)
COLLECTOR_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._+-]*$")
PUBLIC_SOURCE_REF = re.compile(
    r"^https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/(?P<issue>\d+)(?:#.*)?$"
)


def source_issue_number(source_ref: str) -> int | None:
    match = PUBLIC_SOURCE_REF.fullmatch(source_ref)
    return int(match.group("issue")) if match is not None else None


@dataclass(frozen=True)
class AdmissionProvenance:
    observation_id: str
    observed_at: datetime
    collector: str
    source_ref: str

    def as_dict(self) -> dict[str, str]:
        return {
            "collector": self.collector,
            "observation_id": self.observation_id,
            "observed_at": self.observed_at.isoformat(),
            "source_ref": self.source_ref,
        }


def new_admission_provenance(collector: str, source_ref: str) -> AdmissionProvenance:
    return parse_admission_provenance(
        {
            "collector": collector,
            "observation_id": str(uuid4()),
            "observed_at": datetime.now(UTC).isoformat(),
            "source_ref": source_ref,
        }
    )


def parse_admission_provenance(
    value: dict[str, Any],
    *,
    now: datetime | None = None,
) -> AdmissionProvenance:
    observation_id = value.get("observation_id")
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
    if observed_at > current:
        raise ValueError("admission observations are future-dated")
    if current - observed_at > MAX_ADMISSION_AGE:
        raise ValueError("admission observations are stale")
    if not isinstance(collector, str) or not COLLECTOR_ID.fullmatch(collector):
        raise ValueError("admission provenance requires a valid collector identity")
    try:
        parsed_observation_id = UUID(observation_id) if isinstance(observation_id, str) else None
    except ValueError as exc:
        raise ValueError("admission provenance requires a valid observation_id") from exc
    if (
        parsed_observation_id is None
        or parsed_observation_id.version != 4
        or str(parsed_observation_id) != observation_id
    ):
        raise ValueError("admission provenance requires a valid observation_id")
    if (
        not isinstance(source_ref, str)
        or source_issue_number(source_ref) is None
        or contains_private_identity(source_ref)
    ):
        raise ValueError("admission provenance requires a public-safe GitHub issue source")
    return AdmissionProvenance(observation_id, observed_at, collector, source_ref)


def claim_admission_provenance(provenance: AdmissionProvenance, ledger: Path) -> None:
    ledger.mkdir(parents=True, exist_ok=True)
    marker = ledger / f"{provenance.observation_id}.used"
    try:
        descriptor = os.open(marker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ValueError("admission observation provenance has already been consumed") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(f"{provenance.observed_at.isoformat()}\n")


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
