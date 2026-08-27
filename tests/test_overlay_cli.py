from __future__ import annotations

from pathlib import Path
from typing import Any

from conftest import parse_json_output, write_valid_registry


def test_operator_can_validate_an_overlay_without_disclosing_connection_data(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    overlay = tmp_path.parent / "private-overlay.yaml"
    private_values = ["private-host", "operator-user", "vault://fabric/operator-key"]
    overlay.write_text(
        f"""\
schema: heterogeneous-compute-fabric/private-operations-v1
nodes:
  - node_id: compute-01
    hostname: {private_values[0]}
    ssh_user: {private_values[1]}
    credential_references: [{private_values[2]}]
    owners: [operator]
    recovery_locations: [vault://fabric/recovery]
""",
        encoding="utf-8",
    )

    result = run_fabric(
        "overlay",
        "validate",
        "--root",
        str(tmp_path),
        "--overlay",
        str(overlay),
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    assert parse_json_output(result) == {
        "errors": [],
        "nodes": [{"credential_reference_count": 1, "node_id": "compute-01", "status": "joined"}],
        "ok": True,
    }
    for private_value in private_values:
        assert private_value not in result.stdout


def test_overlay_rejects_unknown_duplicate_missing_joins_and_raw_secrets(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    write_valid_registry(tmp_path)
    overlay = tmp_path.parent / "invalid-overlay.yaml"
    raw_secret = "never-print-this-value"
    overlay.write_text(
        f"""\
schema: heterogeneous-compute-fabric/private-operations-v1
nodes:
  - node_id: compute-01
    credential_references: [vault://fabric/key]
  - node_id: compute-01
    credential_references: [vault://fabric/other-key]
  - node_id: unknown-99
    credential_references: []
  - ssh_user: operator
    password: {raw_secret}
""",
        encoding="utf-8",
    )

    result = run_fabric(
        "overlay",
        "validate",
        "--root",
        str(tmp_path),
        "--overlay",
        str(overlay),
        "--format",
        "json",
    )

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "errors": [
            "nodes[1]: duplicate Node Slot join",
            "nodes[2]: unknown Node Slot",
            "nodes[3]: missing node_id",
            "nodes[3]: raw secret field is forbidden",
        ],
        "nodes": [{"credential_reference_count": 1, "node_id": "compute-01", "status": "joined"}],
        "ok": False,
    }
    assert raw_secret not in result.stdout
