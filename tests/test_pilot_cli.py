from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from conftest import parse_json_output, write_valid_registry

HELLO_SHA256 = "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"


def _write_pilot_inputs(tmp_path: Path) -> dict[str, Path]:
    write_valid_registry(tmp_path)
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "architecture": "x86_64",
                "issue_branch": "codex/15-bounded-pilot",
                "repository": "sample",
                "required_roles": ["cpu-build"],
                "source_commit": "0123456789abcdef0123456789abcdef01234567",
                "worktree_isolated": True,
            }
        ),
        encoding="utf-8",
    )
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"hello\n")
    health = tmp_path / "health.txt"
    health.write_text("healthy\n", encoding="utf-8")
    rollback = tmp_path / "rollback.txt"
    rollback.write_text("rollback verified\n", encoding="utf-8")
    return {
        "artifact": artifact,
        "health": health,
        "request": request,
        "rollback": rollback,
    }


def test_authorized_pilot_records_immutable_worker_and_recovery_evidence(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    inputs = _write_pilot_inputs(tmp_path)
    receipt = tmp_path / "deployment-receipt.json"

    result = run_fabric(
        "pilot",
        "--root",
        str(tmp_path),
        "--request",
        str(inputs["request"]),
        "--artifact",
        str(inputs["artifact"]),
        "--health-evidence",
        str(inputs["health"]),
        "--rollback-evidence",
        str(inputs["rollback"]),
        "--receipt",
        str(receipt),
        "--deployment-authorized",
        "--format",
        "json",
    )

    assert result.returncode == 0, result.stderr
    payload = parse_json_output(result)
    assert payload["ok"] is True
    assert payload["worker"] == "compute-01"
    assert payload["artifact"] == {"bytes": 6, "sha256": HELLO_SHA256}
    assert payload["deployment"]["adapter"] == "record-only"
    assert payload["deployment"]["authorized"] is True
    assert payload["issue_branch"] == "codex/15-bounded-pilot"
    assert payload["source_commit"] == "0123456789abcdef0123456789abcdef01234567"
    assert receipt.is_file()
    assert json.loads(receipt.read_text(encoding="utf-8")) == payload


def test_pilot_fails_before_writing_a_receipt_without_deployment_authority(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    inputs = _write_pilot_inputs(tmp_path)
    receipt = tmp_path / "deployment-receipt.json"

    result = run_fabric(
        "pilot",
        "--root",
        str(tmp_path),
        "--request",
        str(inputs["request"]),
        "--artifact",
        str(inputs["artifact"]),
        "--health-evidence",
        str(inputs["health"]),
        "--rollback-evidence",
        str(inputs["rollback"]),
        "--receipt",
        str(receipt),
        "--format",
        "json",
    )

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "error": "explicit deployment authority is required",
        "ok": False,
    }
    assert not receipt.exists()
