from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

CheckStatus = Literal["pass", "fail", "unknown"]
ReportView = Literal["public", "private"]
BASE_CHECKS = (
    "hardware",
    "os_profile",
    "disk",
    "network_ssh",
    "git_worktree",
    "load_thermals",
)
PROFILE_ROLES: dict[str, dict[str, tuple[str, ...]]] = {
    "compute-01": {
        "cpu-build": ("cpu_ram",),
        "ram-build": ("cpu_ram",),
        "batch": ("cpu_ram",),
        "cuda": (
            "nvidia_identity",
            "nvidia_driver",
            "host_gpu_smoke",
            "container_toolkit",
            "gpu_container_smoke",
        ),
        "inference": (
            "nvidia_identity",
            "nvidia_driver",
            "host_gpu_smoke",
            "container_toolkit",
            "gpu_container_smoke",
        ),
    }
}
ALLOWED_OS_PROFILES: dict[str, tuple[str, ...]] = {"compute-01": ("ubuntu24",)}


@dataclass(frozen=True)
class Observation:
    name: str
    status: CheckStatus
    public_evidence: str | None
    private_evidence: str | None

    def as_dict(self, view: ReportView) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "public_evidence": self.public_evidence,
            "status": self.status,
        }
        if view == "private":
            result["private_evidence"] = self.private_evidence
        return result


@dataclass(frozen=True)
class AdmissionReport:
    node_id: str
    profile: str
    node_admission: str
    role_admission: dict[str, str]
    observations: tuple[Observation, ...]
    view: ReportView

    @property
    def ok(self) -> bool:
        return any(state == "schedulable" for state in self.role_admission.values())

    def as_dict(self) -> dict[str, Any]:
        return {
            "checks": [observation.as_dict(self.view) for observation in self.observations],
            "failed_checks": [
                observation.name
                for observation in self.observations
                if observation.status == "fail"
            ],
            "node_admission": self.node_admission,
            "node_id": self.node_id,
            "ok": self.ok,
            "private_details_included": self.view == "private",
            "profile": self.profile,
            "role_admission": dict(sorted(self.role_admission.items())),
            "unknown_checks": [
                observation.name
                for observation in self.observations
                if observation.status == "unknown"
            ],
        }


def _load_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError("observations must contain a mapping")
    return value


def _required_checks(profile: str) -> tuple[str, ...]:
    roles = PROFILE_ROLES.get(profile)
    if roles is None:
        raise ValueError(f"unknown admission profile: {profile}")
    return tuple(
        dict.fromkeys([*BASE_CHECKS, *(check for checks in roles.values() for check in checks)])
    )


def _observation(name: str, values: dict[str, Any]) -> Observation:
    value = values.get(name)
    if not isinstance(value, dict):
        return Observation(name, "unknown", None, None)
    status_value = value.get("status", "unknown")
    if status_value not in {"pass", "fail", "unknown"}:
        raise ValueError(f"{name}: invalid check status")
    public = value.get("public_evidence")
    private = value.get("private_evidence")
    return Observation(
        name,
        status_value,
        public if isinstance(public, str) else None,
        private if isinstance(private, str) else None,
    )


def generate_admission_report(
    profile: str,
    observations_path: Path,
    view: ReportView,
) -> AdmissionReport:
    document = _load_mapping(observations_path)
    if document.get("schema") != "heterogeneous-compute-fabric/admission-observations-v1":
        raise ValueError("observations have an unsupported schema")
    node_id = document.get("node_id")
    if node_id != profile:
        raise ValueError("observation Node Slot does not match the selected profile")
    if document.get("os_profile") not in ALLOWED_OS_PROFILES.get(profile, ()):
        raise ValueError("OS Profile is not allowed for the selected Node Slot")
    values = document.get("checks")
    if not isinstance(values, dict):
        raise ValueError("observations checks must be a mapping")

    observations = tuple(_observation(name, values) for name in _required_checks(profile))
    statuses = {observation.name: observation.status for observation in observations}
    base_passed = all(statuses[name] == "pass" for name in BASE_CHECKS)

    role_admission: dict[str, str] = {}
    for role, role_checks in PROFILE_ROLES[profile].items():
        role_admission[role] = (
            "schedulable"
            if base_passed and all(statuses[name] == "pass" for name in role_checks)
            else "installed"
        )

    if any(state == "schedulable" for state in role_admission.values()):
        node_admission = "schedulable"
    elif base_passed:
        node_admission = "verified"
    else:
        node_admission = "installed"

    return AdmissionReport(
        node_id,
        profile,
        node_admission,
        role_admission,
        observations,
        view,
    )
