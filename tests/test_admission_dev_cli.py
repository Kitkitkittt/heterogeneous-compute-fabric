from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import parse_json_output
from test_admission_compute_cli import BASE_CHECKS

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
                "schema": "heterogeneous-compute-fabric/admission-observations-v1",
                "node_id": "dev-01",
                "role_profile": "workstation",
                "os_profile": os_profile,
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
