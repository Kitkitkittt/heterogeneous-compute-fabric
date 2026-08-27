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
    "cpu_execution",
    "memory_execution",
    "nvidia_identity",
    "nvidia_driver",
    "host_gpu_smoke",
    "container_toolkit",
    "gpu_container_smoke",
]


def _write_compute_observations(path: Path, node_id: str = "compute-02") -> str:
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
                "node_id": node_id,
                "role_profile": "compute",
                "os_profile": "ubuntu24",
                "checks": checks,
            }
        ),
        encoding="utf-8",
    )
    return private_value


def test_compute_report_scales_to_a_new_slot_and_gates_cpu_ram_and_cuda_independently(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    private_value = _write_compute_observations(observations)
    document = json.loads(observations.read_text(encoding="utf-8"))
    document["checks"]["memory_execution"]["status"] = "fail"
    observations.write_text(json.dumps(document), encoding="utf-8")

    result = run_fabric(
        "admission",
        "report",
        "--node-id",
        "compute-02",
        "--role-profile",
        "compute",
        "--os-profile",
        "ubuntu24",
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
    assert payload["node_id"] == "compute-02"
    assert payload["node_admission"] == "schedulable"
    assert payload["role_admission"] == {
        "batch": "installed",
        "cpu-build": "schedulable",
        "cuda": "installed",
        "inference": "installed",
        "ram-build": "installed",
    }
    assert payload["failed_checks"] == ["memory_execution", "host_gpu_smoke"]
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
        "--node-id",
        "compute-02",
        "--role-profile",
        "compute",
        "--os-profile",
        "ubuntu24",
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


def test_public_report_rejects_caller_supplied_private_identity(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    _write_compute_observations(observations)
    document = json.loads(observations.read_text(encoding="utf-8"))
    private_email = "operator" + "@" + "example.com"
    document["checks"]["hardware"]["public_evidence"] = private_email
    observations.write_text(json.dumps(document), encoding="utf-8")

    result = run_fabric(
        "admission",
        "report",
        "--node-id",
        "compute-02",
        "--role-profile",
        "compute",
        "--os-profile",
        "ubuntu24",
        "--observations",
        str(observations),
        "--view",
        "public",
        "--format",
        "json",
    )

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "error": "hardware: public evidence contains prohibited private identity",
        "ok": False,
    }
    assert private_email not in result.stdout


def test_public_report_uses_controlled_summaries_instead_of_caller_text(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    _write_compute_observations(observations)
    document = json.loads(observations.read_text(encoding="utf-8"))
    unclassified_identity = "opaque-machine-identity"
    document["checks"]["hardware"]["public_evidence"] = unclassified_identity
    observations.write_text(json.dumps(document), encoding="utf-8")

    result = run_fabric(
        "admission",
        "report",
        "--node-id",
        "compute-02",
        "--role-profile",
        "compute",
        "--os-profile",
        "ubuntu24",
        "--observations",
        str(observations),
        "--view",
        "public",
        "--format",
        "json",
    )

    assert result.returncode == 0
    assert unclassified_identity not in result.stdout
    hardware = parse_json_output(result)["checks"][0]
    assert hardware["public_evidence"] == "hardware check pass"


def test_fixture_probe_adapter_collects_private_results_without_printing_them(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    probe_results = tmp_path / "probe-results.json"
    secret_detail = "private-machine-observation"
    pass_outputs = {
        "hardware": ["Architecture: x86_64", "Mem: 48000000000"],
        "os_profile": ['ID=ubuntu\nVERSION_ID="24.04"'],
        "disk": [
            '{"blockdevices":[{"name":"disk"}]}',
            '{"all_healthy":true,"disk_count":1}',
        ],
        "network_ssh": [
            "pong from private peer",
            "",
            "pubkeyauthentication yes\npasswordauthentication no",
        ],
        "git_worktree": ["true", "/repo/.git/worktrees/issue", ""],
        "load_thermals": ["bounded-load-ok", '{"temp1_input":42.0}'],
        "cpu_execution": ["333328333350000"],
        "memory_execution": ["16777216"],
        "nvidia_identity": ["NVIDIA GPU, 16384 MiB"],
        "nvidia_driver": ["560.1"],
        "host_gpu_smoke": ["cuda-smoke-ok"],
        "container_toolkit": ["NVIDIA Container Toolkit CLI version 1.17.0"],
        "gpu_container_smoke": ["NVIDIA GPU"],
    }
    probe_results.write_text(
        json.dumps(
            {
                name: {
                    "returncode": 0,
                    "outputs": pass_outputs[name],
                    "stderr": secret_detail,
                }
                for name in [*BASE_CHECKS, *COMPUTE_CHECKS]
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "observations.json"

    result = run_fabric(
        "admission",
        "collect",
        "--node-id",
        "compute-02",
        "--role-profile",
        "compute",
        "--os-profile",
        "ubuntu24",
        "--adapter",
        "fixture",
        "--probe-results",
        str(probe_results),
        "--output",
        str(output),
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    assert secret_detail not in result.stdout
    assert parse_json_output(result) == {
        "check_count": len([*BASE_CHECKS, *COMPUTE_CHECKS]),
        "node_id": "compute-02",
        "ok": True,
        "output_written": True,
        "role_profile": "compute",
    }
    collected = json.loads(output.read_text(encoding="utf-8"))
    assert collected["checks"]["hardware"]["status"] == "pass"
    assert secret_detail in collected["checks"]["hardware"]["private_evidence"]


def test_zero_exit_docker_info_does_not_pass_the_gpu_container_smoke(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    probe_results = tmp_path / "probe-results.json"
    probe_results.write_text(
        json.dumps(
            {
                "gpu_container_smoke": {
                    "returncode": 0,
                    "outputs": ["Server Version: 27.0"],
                    "stderr": "",
                }
            }
        ),
        encoding="utf-8",
    )
    output = tmp_path / "observations.json"

    result = run_fabric(
        "admission",
        "collect",
        "--node-id",
        "compute-02",
        "--role-profile",
        "compute",
        "--os-profile",
        "ubuntu24",
        "--adapter",
        "fixture",
        "--probe-results",
        str(probe_results),
        "--output",
        str(output),
        "--format",
        "json",
    )

    assert result.returncode == 0
    collected = json.loads(output.read_text(encoding="utf-8"))
    assert collected["checks"]["gpu_container_smoke"]["status"] == "fail"
