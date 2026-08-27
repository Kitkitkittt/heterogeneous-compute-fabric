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
