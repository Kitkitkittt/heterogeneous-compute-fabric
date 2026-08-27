from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import append_node, parse_json_output, write_valid_registry


def test_user_can_route_work_to_every_eligible_node(tmp_path: Path, run_fabric: Any) -> None:
    write_valid_registry(tmp_path)
    append_node(
        tmp_path,
        """\
  - node_id: compute-02
    admission_state: schedulable
    roles: [cpu-build]
    role_admission: {cpu-build: schedulable}
    admission_evidence: {status: verified, observed_at: 2026-08-27, source: acceptance-report}
    role_admission_evidence:
      cpu-build: {status: verified, observed_at: 2026-08-27, source: acceptance-report}
    task_label: node:compute-02
    hardware:
      cpu:
        architecture: x86_64
        evidence:
          {status: verified, lifetime: chassis, observed_at: 2026-08-27,
           source: hardware-audit}
    admission_gates: [hardware-verified]
""",
    )
    repositories = tmp_path / "inventory" / "repositories.yaml"
    repositories.write_text(
        repositories.read_text(encoding="utf-8").replace(
            "eligible_nodes: [compute-01]",
            "eligible_nodes: [compute-01, compute-02]",
        ),
        encoding="utf-8",
    )

    result = run_fabric(
        "route",
        "--root",
        str(tmp_path),
        "--repository",
        "sample",
        "--architecture",
        "x86_64",
        "--role",
        "cpu-build",
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    assert parse_json_output(result) == {
        "decisions": [
            {"eligible": True, "node_id": "compute-01", "reasons": []},
            {"eligible": True, "node_id": "compute-02", "reasons": []},
        ],
        "eligible_nodes": ["compute-01", "compute-02"],
        "ok": True,
    }


def test_routing_explains_architecture_role_and_admission_failures(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    append_node(
        tmp_path,
        """\
  - node_id: cloud-01
    admission_state: schedulable
    roles: [arm64-build]
    role_admission: {arm64-build: schedulable}
    admission_evidence: {status: verified, observed_at: 2026-08-27, source: acceptance-report}
    role_admission_evidence:
      arm64-build: {status: verified, observed_at: 2026-08-27, source: acceptance-report}
    task_label: node:cloud-01
    hardware:
      cpu:
        architecture: arm64
        evidence:
          {status: verified, lifetime: chassis, observed_at: 2026-08-27,
           source: hardware-audit}
    admission_gates: [cost-confirmed]
  - node_id: compute-02
    admission_state: verified
    roles: [cpu-build]
    role_admission: {cpu-build: verified}
    task_label: node:compute-02
    hardware:
      cpu:
        architecture: x86_64
        evidence: {status: verified, lifetime: chassis}
    admission_gates: [hardware-verified]
""",
    )
    repositories = tmp_path / "inventory" / "repositories.yaml"
    repositories.write_text(
        repositories.read_text(encoding="utf-8").replace(
            "eligible_nodes: [compute-01]",
            "eligible_nodes: [compute-01, cloud-01, compute-02]",
        ),
        encoding="utf-8",
    )

    result = run_fabric(
        "route",
        "--root",
        str(tmp_path),
        "--repository",
        "sample",
        "--architecture",
        "x86_64",
        "--role",
        "cuda",
        "--format",
        "json",
    )

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "decisions": [
            {
                "eligible": False,
                "node_id": "cloud-01",
                "reasons": [
                    "architecture mismatch",
                    "missing Role: cpu-build",
                    "missing Role: cuda",
                ],
            },
            {
                "eligible": False,
                "node_id": "compute-01",
                "reasons": ["missing Role: cuda"],
            },
            {
                "eligible": False,
                "node_id": "compute-02",
                "reasons": [
                    "node is not schedulable",
                    "node admission evidence is not directly verified",
                    "architecture evidence is not directly verified",
                    "Role is not schedulable: cpu-build",
                    "missing Role: cuda",
                ],
            },
        ],
        "eligible_nodes": [],
        "ok": False,
    }


def test_routing_rejects_inherited_admission_evidence(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    nodes = tmp_path / "inventory" / "nodes.yaml"
    nodes.write_text(
        nodes.read_text(encoding="utf-8")
        .replace(
            "    admission_evidence:\n      status: verified",
            "    admission_evidence:\n      status: inherited",
        )
        .replace(
            "status: verified, observed_at: 2026-08-27, source: acceptance-report",
            "status: inherited, observed_at: 2026-08-27, source: prior-handoff",
        ),
        encoding="utf-8",
    )

    result = run_fabric(
        "route",
        "--root",
        str(tmp_path),
        "--repository",
        "sample",
        "--architecture",
        "x86_64",
        "--role",
        "cpu-build",
        "--format",
        "json",
    )

    assert result.returncode == 1
    assert parse_json_output(result)["decisions"] == [
        {
            "eligible": False,
            "node_id": "compute-01",
            "reasons": [
                "node admission evidence is not directly verified",
                "Role admission evidence is not directly verified: cpu-build",
            ],
        }
    ]
