from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import parse_json_output, write_valid_registry


def _issue(
    number: int,
    *,
    state: str = "OPEN",
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
    blocked_by: int = 0,
) -> dict[str, Any]:
    return {
        "assignees": [{"login": value} for value in (assignees or [])],
        "issue_dependencies_summary": {"blocked_by": blocked_by},
        "labels": [{"name": value} for value in (labels or [])],
        "number": number,
        "state": state,
        "title": f"Issue {number}",
    }


def test_frontier_lists_only_open_unassigned_unblocked_work(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    issues = tmp_path / "issues.json"
    issues.write_text(
        json.dumps(
            [
                _issue(12, labels=["ready-for-agent", "node:compute-01"]),
                _issue(13, labels=["ready-for-human"], blocked_by=1),
                _issue(14, labels=["ready-for-agent"], assignees=["worker"]),
                _issue(15, state="CLOSED", labels=["ready-for-agent"]),
                _issue(16, labels=["needs-triage"]),
                _issue(17, labels=["wontfix"]),
            ]
        ),
        encoding="utf-8",
    )

    result = run_fabric(
        "frontier",
        "--root",
        str(tmp_path),
        "--issues-file",
        str(issues),
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    assert parse_json_output(result) == {
        "frontier": [
            {
                "next_actor": "agent",
                "node_conflicts": [],
                "number": 12,
                "suitable_nodes": ["compute-01"],
                "title": "Issue 12",
            },
            {
                "next_actor": "maintainer",
                "node_conflicts": [],
                "number": 16,
                "suitable_nodes": [],
                "title": "Issue 16",
            },
        ],
        "ok": True,
    }


def test_frontier_reports_suitability_without_claiming_node_readiness(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    nodes = tmp_path / "inventory" / "nodes.yaml"
    nodes.write_text(
        nodes.read_text(encoding="utf-8").replace(
            "admission_state: schedulable",
            "admission_state: install_pending",
        ),
        encoding="utf-8",
    )
    issues = tmp_path / "issues.json"
    issues.write_text(
        json.dumps([_issue(12, labels=["ready-for-agent", "node:compute-01"])]),
        encoding="utf-8",
    )

    result = run_fabric(
        "frontier",
        "--root",
        str(tmp_path),
        "--issues-file",
        str(issues),
        "--format",
        "json",
    )

    assert result.returncode == 0
    assert parse_json_output(result)["frontier"][0] == {
        "next_actor": "agent",
        "node_conflicts": [{"admission_state": "install_pending", "node_id": "compute-01"}],
        "number": 12,
        "suitable_nodes": ["compute-01"],
        "title": "Issue 12",
    }
