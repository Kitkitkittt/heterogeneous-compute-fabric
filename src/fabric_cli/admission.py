from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fabric_cli.evidence import (
    ADMISSION_SCHEMA,
    AdmissionProvenance,
    claim_admission_provenance,
    parse_admission_provenance,
)
from fabric_cli.io import load_mapping
from fabric_cli.safety import contains_private_identity

CheckStatus = Literal["pass", "fail", "unknown"]
ReportView = Literal["public", "private"]
BASE_CHECKS = (
    "hardware",
    "os_profile",
    "disk",
    "disk_encryption_headroom",
    "time_sync",
    "software_updates",
    "firewall",
    "network_ssh",
    "git_worktree",
    "container_execution",
    "load_thermals",
)
GPU_CHECKS = (
    "nvidia_identity",
    "nvidia_driver",
    "host_gpu_smoke",
    "container_toolkit",
    "gpu_container_smoke",
)
WORKSTATION_CHECKS = (
    "displays",
    "browser_acceleration",
    "suspend_resume",
    "shutdown_reboot",
    "ethernet",
    "wifi",
    "bluetooth",
    "audio",
    "usb",
    "editor_toolchain",
    "containers",
    "graphics_smoke",
)
ROLE_PROFILE_REQUIREMENTS: dict[str, dict[str, tuple[str, ...]]] = {
    "compute": {
        "cpu-build": ("cpu_execution",),
        "ram-build": ("memory_execution",),
        "batch": ("cpu_execution", "memory_execution"),
        "cuda": GPU_CHECKS,
        "inference": GPU_CHECKS,
    },
    "workstation": {
        "interactive-development": WORKSTATION_CHECKS,
        "control": WORKSTATION_CHECKS,
        "light-test": WORKSTATION_CHECKS,
    },
}
ALLOWED_OS_PROFILES: dict[str, tuple[str, ...]] = {
    "compute": ("ubuntu24",),
    "workstation": ("ubuntu24", "ubuntu26", "pop24"),
}
POP_PROFILE_CHECKS = ("secure_boot_policy", "profile_upgrade_path")


@dataclass(frozen=True)
class Observation:
    name: str
    status: CheckStatus
    public_evidence: str | None
    private_evidence: str | None

    def as_dict(self, view: ReportView) -> dict[str, Any]:
        public_evidence = (
            f"{self.name} check {self.status}" if view == "public" else self.public_evidence
        )
        result: dict[str, Any] = {
            "name": self.name,
            "public_evidence": public_evidence,
            "status": self.status,
        }
        if view == "private":
            result["private_evidence"] = self.private_evidence
        return result


@dataclass(frozen=True)
class AdmissionReport:
    node_id: str
    role_profile: str
    os_profile: str
    node_admission: str
    role_admission: dict[str, str]
    observations: tuple[Observation, ...]
    provenance: AdmissionProvenance
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
            "os_profile": self.os_profile,
            **self.provenance.as_dict(),
            "private_details_included": self.view == "private",
            "role_admission": dict(sorted(self.role_admission.items())),
            "role_profile": self.role_profile,
            "unknown_checks": [
                observation.name
                for observation in self.observations
                if observation.status == "unknown"
            ],
        }


def role_requirements(role_profile: str, os_profile: str) -> dict[str, tuple[str, ...]]:
    base_roles = ROLE_PROFILE_REQUIREMENTS.get(role_profile)
    if base_roles is None:
        raise ValueError(f"unknown admission role profile: {role_profile}")
    if os_profile not in ALLOWED_OS_PROFILES[role_profile]:
        raise ValueError("OS Profile is not allowed for the selected Role profile")
    if role_profile == "workstation" and os_profile == "pop24":
        return {role: (*checks, *POP_PROFILE_CHECKS) for role, checks in base_roles.items()}
    return base_roles


def validate_profile_assignment(node_id: str, role_profile: str, os_profile: str) -> None:
    role_requirements(role_profile, os_profile)
    if os_profile == "ubuntu26" and node_id != "dev-01":
        raise ValueError("ubuntu26 OS Profile is allowed only for dev-01")


def required_checks(role_profile: str, os_profile: str) -> tuple[str, ...]:
    roles = role_requirements(role_profile, os_profile)
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
    if isinstance(public, str) and contains_private_identity(public):
        raise ValueError(f"{name}: public evidence contains prohibited private identity")
    return Observation(
        name,
        status_value,
        public if isinstance(public, str) else None,
        private if isinstance(private, str) else None,
    )


def generate_admission_report(
    node_id: str,
    role_profile: str,
    os_profile: str,
    observations_path: Path,
    replay_ledger: Path,
    view: ReportView,
) -> AdmissionReport:
    validate_profile_assignment(node_id, role_profile, os_profile)
    document = load_mapping(observations_path, "observations")
    if document.get("schema") != ADMISSION_SCHEMA:
        raise ValueError("observations have an unsupported schema")
    provenance = parse_admission_provenance(document)
    if document.get("node_id") != node_id:
        raise ValueError("observation Node Slot does not match --node-id")
    if document.get("role_profile") != role_profile:
        raise ValueError("observation Role profile does not match --role-profile")
    if document.get("os_profile") != os_profile:
        raise ValueError("observation OS Profile does not match --os-profile")
    values = document.get("checks")
    if not isinstance(values, dict):
        raise ValueError("observations checks must be a mapping")

    roles = role_requirements(role_profile, os_profile)
    observations = tuple(
        _observation(name, values) for name in required_checks(role_profile, os_profile)
    )
    statuses = {observation.name: observation.status for observation in observations}
    base_passed = all(statuses[name] == "pass" for name in BASE_CHECKS)
    role_admission = {
        role: (
            "schedulable"
            if base_passed and all(statuses[name] == "pass" for name in role_checks)
            else "installed"
        )
        for role, role_checks in roles.items()
    }
    if any(state == "schedulable" for state in role_admission.values()):
        node_admission = "schedulable"
    elif base_passed:
        node_admission = "verified"
    else:
        node_admission = "installed"

    report = AdmissionReport(
        node_id,
        role_profile,
        os_profile,
        node_admission,
        role_admission,
        observations,
        provenance,
        view,
    )
    claim_admission_provenance(provenance, replay_ledger)
    return report
