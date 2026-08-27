from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import parse_json_output, write_valid_registry


def test_user_can_validate_a_fresh_public_registry(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 0, result.stderr
    assert parse_json_output(result) == {
        "checks": [
            {"errors": [], "name": "registries", "ok": True},
            {"errors": [], "name": "links", "ok": True},
            {"errors": [], "name": "diagrams", "ok": True},
            {"errors": [], "name": "public-safety", "ok": True},
        ],
        "ok": True,
    }


def test_validation_fails_closed_without_repeating_a_private_pattern(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    private_value = "operator-private-host"
    (tmp_path / "README.md").write_text(private_value, encoding="utf-8")
    patterns = tmp_path.parent / "private-patterns.txt"
    patterns.write_text(private_value, encoding="utf-8")

    result = run_fabric(
        "validate",
        "--root",
        str(tmp_path),
        "--prohibited-patterns",
        str(patterns),
        "--format",
        "json",
    )

    assert result.returncode == 1
    payload = parse_json_output(result)
    assert payload["ok"] is False
    assert payload["checks"][-1] == {
        "errors": ["README.md: configured prohibited public pattern matched"],
        "name": "public-safety",
        "ok": False,
    }
    assert private_value not in result.stdout


def test_validation_reports_registry_and_link_contract_failures(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    nodes_path = tmp_path / "inventory" / "nodes.yaml"
    nodes_path.write_text(
        nodes_path.read_text(encoding="utf-8").replace(
            "admission_state: schedulable",
            "admission_state: hopeful",
        ),
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("[Missing](missing.md)\n", encoding="utf-8")

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    payload = parse_json_output(result)
    assert payload["checks"][0]["errors"] == ["compute-01: invalid Admission State"]
    assert payload["checks"][1]["errors"] == ["README.md has a missing link target"]


def test_validation_rejects_schedulable_roles_without_direct_admission_evidence(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    nodes_path = tmp_path / "inventory" / "nodes.yaml"
    text = nodes_path.read_text(encoding="utf-8")
    start = text.index("    admission_evidence:")
    end = text.index("    task_label:", start)
    nodes_path.write_text(text[:start] + text[end:], encoding="utf-8")

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    errors = parse_json_output(result)["checks"][0]["errors"]
    assert errors == [
        "compute-01: schedulable node requires directly verified admission evidence",
        "compute-01: schedulable Role cpu-build requires directly verified admission evidence",
    ]


def test_validation_requires_a_real_iso_observation_date(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    nodes_path = tmp_path / "inventory" / "nodes.yaml"
    nodes_path.write_text(
        nodes_path.read_text(encoding="utf-8").replace(
            "observed_at: 2026-08-27",
            "observed_at: false",
        ),
        encoding="utf-8",
    )

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    assert parse_json_output(result)["checks"][0]["errors"] == [
        "compute-01: schedulable node requires directly verified admission evidence",
        "compute-01: schedulable Role cpu-build requires directly verified admission evidence",
    ]


def test_validation_checks_complete_repository_contract_and_common_private_patterns(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    repositories = tmp_path / "inventory" / "repositories.yaml"
    repositories.write_text(
        repositories.read_text(encoding="utf-8").replace("    bootstrap_command: uv sync\n", ""),
        encoding="utf-8",
    )
    private_email = "operator" + "@" + "example.com"
    private_address = ".".join(("192", "168", "1", "20"))
    private_path = "/".join(("", "home", "operator", "project"))
    (tmp_path / "generated.json").write_text(
        f'{{"contact":"{private_email}","address":"{private_address}","path":"{private_path}"}}',
        encoding="utf-8",
    )

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    payload = parse_json_output(result)
    assert payload["checks"][0]["errors"] == ["sample: bootstrap_command is required"]
    assert payload["checks"][-1]["errors"] == [
        "generated.json: generic prohibited public pattern matched"
    ]


def test_validation_requires_evidence_for_important_hardware_facts(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    nodes_path = tmp_path / "inventory" / "nodes.yaml"
    nodes_path.write_text(
        nodes_path.read_text(encoding="utf-8").replace(
            "        evidence: {status: verified, lifetime: chassis}\n      cpu:",
            "      cpu:",
        ),
        encoding="utf-8",
    )

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    assert parse_json_output(result)["checks"][0]["errors"] == [
        "compute-01: hardware.system requires evidence"
    ]


def test_validation_rejects_stale_or_illegible_diagram_outputs(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    diagram = tmp_path / "docs" / "diagrams" / "fabric.mmd"
    diagram.write_text(diagram.read_text(encoding="utf-8") + "B-->C\n", encoding="utf-8")

    result = run_fabric("validate", "--root", str(tmp_path), "--format", "json")

    assert result.returncode == 1
    assert parse_json_output(result)["checks"][2]["errors"] == [
        "fabric.mmd does not match the render manifest"
    ]
