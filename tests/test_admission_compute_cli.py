from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from uuid import uuid4

from conftest import parse_json_output

from fabric_cli.cli import _current_worktree_root
from fabric_cli.probes import _disk_policy_script, _issue_branch_matches_source

BASE_CHECKS = [
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


def test_worktree_source_and_encryption_probes_fail_closed() -> None:
    assert _issue_branch_matches_source(
        "codex/12-compute-admission",
        "https://github.com/owner/repository/issues/12",
    )
    assert not _issue_branch_matches_source(
        "codex/12-compute-admission",
        "https://github.com/owner/repository/issues/13",
    )
    assert not _issue_branch_matches_source(
        "codex/12-compute-admission",
        "https://github.com/owner/repository/pull/12",
    )
    script = _disk_policy_script(True, 1)
    assert "['lsblk', '-s', '-n', '-o', 'TYPE', source]" in script
    assert "encrypted = 'crypt' in types" in script
    assert "source.startswith('/dev/mapper/')" not in script


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
                "schema": "heterogeneous-compute-fabric/admission-observations-v2",
                "node_id": node_id,
                "role_profile": "compute",
                "os_profile": "ubuntu24",
                "observation_id": str(uuid4()),
                "observed_at": datetime.now(UTC).isoformat(),
                "collector": "fabric-cli/fixture-v1",
                "source_ref": "https://github.com/owner/repository/issues/12",
                "checks": checks,
            }
        ),
        encoding="utf-8",
    )
    return private_value


def _write_issue_evidence(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "assignees": ["owner"],
                "blocked_by": [],
                "number": 12,
                "repository": "owner/repository",
                "state": "OPEN",
                "status": "verified",
                "worktree_binding": {
                    "base": "main",
                    "branch": "codex/12-compute-admission",
                    "role": "direct",
                },
            }
        ),
        encoding="utf-8",
    )


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
        "--replay-ledger",
        str(tmp_path / "replay-ledger"),
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
        "--replay-ledger",
        str(tmp_path / "replay-ledger"),
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
        "--replay-ledger",
        str(tmp_path / "replay-ledger"),
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
        "--replay-ledger",
        str(tmp_path / "replay-ledger"),
        "--view",
        "public",
        "--format",
        "json",
    )

    assert result.returncode == 0
    assert unclassified_identity not in result.stdout
    hardware = parse_json_output(result)["checks"][0]
    assert hardware["public_evidence"] == "hardware check pass"


def test_admission_report_rejects_missing_stale_future_or_private_provenance(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    mutations = (
        (
            "v1",
            lambda document: document.__setitem__(
                "schema", "heterogeneous-compute-fabric/admission-observations-v1"
            ),
        ),
        ("missing", lambda document: document.pop("observed_at")),
        ("missing-id", lambda document: document.pop("observation_id")),
        ("collector", lambda document: document.__setitem__("collector", "not valid")),
        (
            "stale",
            lambda document: document.__setitem__(
                "observed_at", (datetime.now(UTC) - timedelta(hours=25)).isoformat()
            ),
        ),
        (
            "future",
            lambda document: document.__setitem__(
                "observed_at", (datetime.now(UTC) + timedelta(minutes=1)).isoformat()
            ),
        ),
        (
            "private",
            lambda document: document.__setitem__(
                "source_ref",
                "https://example.invalid/private/operator" + "@" + "example.com",
            ),
        ),
    )

    for name, mutate in mutations:
        _write_compute_observations(observations)
        document = json.loads(observations.read_text(encoding="utf-8"))
        mutate(document)
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
            "--replay-ledger",
            str(tmp_path / "replay-ledger"),
            "--format",
            "json",
        )

        assert result.returncode == 1, name
        assert json.loads(result.stdout)["ok"] is False


def test_admission_report_consumes_each_observation_id_once(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    replay_ledger = tmp_path / "replay-ledger"
    _write_compute_observations(observations)
    command = (
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
        "--replay-ledger",
        str(replay_ledger),
        "--format",
        "json",
    )

    first = run_fabric(*command)
    replay = run_fabric(*command)

    assert first.returncode == 0
    assert replay.returncode == 1
    assert parse_json_output(replay) == {
        "error": "admission observation provenance has already been consumed",
        "ok": False,
    }


def test_admission_report_rejects_a_replay_ledger_inside_the_public_worktree(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    observations = tmp_path / "compute-observations.json"
    forbidden_ledger = Path.cwd() / f".test-replay-ledger-{uuid4()}"
    _write_compute_observations(observations)

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
        "--replay-ledger",
        str(forbidden_ledger),
        "--format",
        "json",
    )

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "error": "private replay ledger must be outside the current worktree",
        "ok": False,
    }
    assert not forbidden_ledger.exists()


def test_current_worktree_root_is_not_narrowed_to_the_invocation_directory(
    monkeypatch: Any,
) -> None:
    worktree_root = Path.cwd().resolve()
    monkeypatch.chdir(worktree_root / "src" / "fabric_cli")

    assert _current_worktree_root() == worktree_root


def test_fixture_probe_adapter_collects_private_results_without_printing_them(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    probe_results = tmp_path / "probe-results.json"
    issue_evidence = tmp_path / "issue-evidence.json"
    _write_issue_evidence(issue_evidence)
    secret_detail = "private-machine-observation"
    pass_outputs = {
        "hardware": ["Architecture: x86_64", "Mem: 48000000000"],
        "os_profile": ['ID=ubuntu\nVERSION_ID="24.04"'],
        "disk": [
            '{"blockdevices":[{"name":"disk"}]}',
            '{"all_healthy":true,"disk_count":1}',
        ],
        "disk_encryption_headroom": [
            '{"encrypted":false,"encryption_required":false,'
            '"free_bytes":107374182400,"minimum_free_bytes":53687091200,'
            '"policy_match":true}'
        ],
        "time_sync": ["yes"],
        "software_updates": ["0 upgraded, 0 newly installed, 0 to remove"],
        "firewall": ["Status: active"],
        "network_ssh": [
            "pong from private peer",
            "",
            "pubkeyauthentication yes\npasswordauthentication no",
        ],
        "git_worktree": [
            "true",
            "/repo/.git/worktrees/issue",
            "/repo/.git",
            "codex/12-compute-admission",
            "",
        ],
        "container_execution": ["container-smoke-ok"],
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
        "--issue-evidence",
        str(issue_evidence),
        "--source-ref",
        "https://github.com/owner/repository/issues/12",
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
    assert collected["collector"] == "fabric-cli/fixture-v1"
    assert collected["observation_id"]
    assert collected["source_ref"] == "https://github.com/owner/repository/issues/12"
    assert collected["observed_at"].endswith("+00:00")


def test_zero_exit_docker_info_does_not_pass_the_gpu_container_smoke(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    probe_results = tmp_path / "probe-results.json"
    issue_evidence = tmp_path / "issue-evidence.json"
    _write_issue_evidence(issue_evidence)
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
        "--issue-evidence",
        str(issue_evidence),
        "--source-ref",
        "https://github.com/owner/repository/issues/12",
        "--output",
        str(output),
        "--format",
        "json",
    )

    assert result.returncode == 0
    collected = json.loads(output.read_text(encoding="utf-8"))
    assert collected["checks"]["gpu_container_smoke"]["status"] == "fail"
