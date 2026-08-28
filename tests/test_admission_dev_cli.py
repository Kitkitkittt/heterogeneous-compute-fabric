from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest
from conftest import parse_json_output
from test_admission_compute_cli import BASE_CHECKS

from fabric_cli.admission import role_requirements, validate_profile_assignment
from fabric_cli.probes import _semantic_pass

WORKSTATION_CHECKS = [
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
]


def test_ubuntu26_profile_requires_the_exact_release() -> None:
    assert _semantic_pass(
        "os_profile",
        ('ID=ubuntu\nVERSION_ID="26.04"',),
        "ubuntu26",
        "https://github.com/owner/repository/issues/26",
    )
    assert not _semantic_pass(
        "os_profile",
        ('ID=ubuntu\nVERSION_ID="24.04"',),
        "ubuntu26",
        "https://github.com/owner/repository/issues/26",
    )


def test_ubuntu26_is_workstation_only() -> None:
    assert role_requirements("workstation", "ubuntu26")
    validate_profile_assignment("dev-01", "workstation", "ubuntu26")
    with pytest.raises(ValueError, match="OS Profile is not allowed"):
        role_requirements("compute", "ubuntu26")
    with pytest.raises(ValueError, match="allowed only for dev-01"):
        validate_profile_assignment("dev-02", "workstation", "ubuntu26")


def _write_dev_observations(path: Path, os_profile: str, include_pop_gate: bool) -> None:
    checks = {
        name: {"status": "pass", "public_evidence": f"{name} passed"}
        for name in [*BASE_CHECKS, *WORKSTATION_CHECKS]
    }
    if os_profile == "pop24":
        checks["profile_upgrade_path"] = {
            "status": "pass",
            "public_evidence": "upgrade path recorded",
        }
        if include_pop_gate:
            checks["secure_boot_policy"] = {
                "status": "pass",
                "public_evidence": "policy recorded",
            }
    path.write_text(
        json.dumps(
            {
                "schema": "heterogeneous-compute-fabric/admission-observations-v2",
                "node_id": "dev-01",
                "role_profile": "workstation",
                "os_profile": os_profile,
                "observation_id": str(uuid4()),
                "observed_at": datetime.now(UTC).isoformat(),
                "collector": "fabric-cli/fixture-v1",
                "source_ref": "https://github.com/owner/repository/issues/13",
                "checks": checks,
            }
        ),
        encoding="utf-8",
    )


def test_dev_report_admits_a_complete_ubuntu_workstation(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "dev-observations.json"
    _write_dev_observations(observations, "ubuntu24", include_pop_gate=False)

    result = run_fabric(
        "admission",
        "report",
        "--node-id",
        "dev-01",
        "--role-profile",
        "workstation",
        "--os-profile",
        "ubuntu24",
        "--observations",
        str(observations),
        "--replay-ledger",
        str(tmp_path / "replay-ledger"),
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    payload = parse_json_output(result)
    assert payload["node_admission"] == "schedulable"
    assert payload["role_admission"] == {
        "control": "schedulable",
        "interactive-development": "schedulable",
        "light-test": "schedulable",
    }
    assert payload["failed_checks"] == []
    assert payload["unknown_checks"] == []


def test_pop_workstation_stays_gated_without_its_profile_specific_policy(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "pop-observations.json"
    _write_dev_observations(observations, "pop24", include_pop_gate=False)

    result = run_fabric(
        "admission",
        "report",
        "--node-id",
        "dev-01",
        "--role-profile",
        "workstation",
        "--os-profile",
        "pop24",
        "--observations",
        str(observations),
        "--replay-ledger",
        str(tmp_path / "replay-ledger"),
        "--format",
        "json",
    )

    assert result.returncode == 1
    payload = parse_json_output(result)
    assert payload["node_admission"] == "verified"
    assert payload["role_admission"] == {
        "control": "installed",
        "interactive-development": "installed",
        "light-test": "installed",
    }
    assert payload["unknown_checks"] == ["secure_boot_policy"]
