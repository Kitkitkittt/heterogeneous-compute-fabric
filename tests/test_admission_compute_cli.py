from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import parse_json_output

BASE_CHECKS = [
    "hardware",
    "os_profile",
    "disk",
    "network_ssh",
    "git_worktree",
    "load_thermals",
]
COMPUTE_CHECKS = [
    "cpu_ram",
    "nvidia_identity",
    "nvidia_driver",
    "host_gpu_smoke",
    "container_toolkit",
    "gpu_container_smoke",
]


def _write_compute_observations(path: Path) -> str:
    private_value = "private-device-and-route-detail"
    checks = {
        name: {
            "status": "pass",
            "public_evidence": f"{name} passed",
            "private_evidence": private_value,
        }
        for name in [*BASE_CHECKS, *COMPUTE_CHECKS]
    }
    checks["host_gpu_smoke"]["status"] = "fail"
    checks["gpu_container_smoke"]["status"] = "unknown"
    path.write_text(
        json.dumps(
            {
                "schema": "heterogeneous-compute-fabric/admission-observations-v1",
                "node_id": "compute-01",
                "os_profile": "ubuntu24",
                "checks": checks,
            }
        ),
        encoding="utf-8",
    )
    return private_value


def test_compute_report_admits_cpu_roles_but_keeps_failed_cuda_roles_gated(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    private_value = _write_compute_observations(observations)

    result = run_fabric(
        "admission",
        "report",
        "--profile",
        "compute-01",
        "--observations",
        str(observations),
        "--view",
        "public",
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    payload = parse_json_output(result)
    assert payload["ok"] is True
    assert payload["node_id"] == "compute-01"
    assert payload["node_admission"] == "schedulable"
    assert payload["role_admission"] == {
        "batch": "schedulable",
        "cpu-build": "schedulable",
        "cuda": "installed",
        "inference": "installed",
        "ram-build": "schedulable",
    }
    assert payload["failed_checks"] == ["host_gpu_smoke"]
    assert payload["unknown_checks"] == ["gpu_container_smoke"]
    assert payload["private_details_included"] is False
    assert private_value not in result.stdout


def test_private_compute_report_requires_an_explicit_view(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    private_value = _write_compute_observations(observations)

    result = run_fabric(
        "admission",
        "report",
        "--profile",
        "compute-01",
        "--observations",
        str(observations),
        "--view",
        "private",
        "--format",
        "json",
    )

    assert result.returncode == 0
    payload = parse_json_output(result)
    assert payload["private_details_included"] is True
    assert private_value in result.stdout
