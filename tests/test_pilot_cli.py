from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from conftest import parse_json_output, write_valid_registry

HELLO_SHA256 = "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"


def _write_pilot_inputs(tmp_path: Path) -> dict[str, Path]:
    write_valid_registry(tmp_path)
    source = tmp_path / "source"
    source.mkdir()
    subprocess.run(["git", "init", "-b", "main"], cwd=source, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test" + "@" + "example.invalid"],
        cwd=source,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test Operator"], cwd=source, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://github.com/owner/repository.git"],
        cwd=source,
        check=True,
    )
    (source / "source.txt").write_text("immutable source\n", encoding="utf-8")
    subprocess.run(["git", "add", "source.txt"], cwd=source, check=True)
    subprocess.run(["git", "commit", "-m", "test: immutable source"], cwd=source, check=True)
    worktree = tmp_path / "issue-worktree"
    subprocess.run(
        ["git", "worktree", "add", "-b", "codex/15-bounded-pilot", str(worktree)],
        cwd=source,
        check=True,
        capture_output=True,
    )
    source_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=worktree,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "architecture": "x86_64",
                "issue_branch": "codex/15-bounded-pilot",
                "repository": "sample",
                "required_roles": ["cpu-build"],
                "source_commit": source_commit,
            }
        ),
        encoding="utf-8",
    )
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"hello\n")
    health = tmp_path / "health.txt"
    health.write_text(
        json.dumps({"source_commit": source_commit, "status": "pass", "summary": "healthy"}),
        encoding="utf-8",
    )
    rollback = tmp_path / "rollback.txt"
    rollback.write_text(
        json.dumps(
            {"source_commit": source_commit, "status": "pass", "summary": "rollback verified"}
        ),
        encoding="utf-8",
    )
    issue = tmp_path / "issue.json"
    issue.write_text(
        json.dumps(
            {
                "assignees": ["owner"],
                "blocked_by": [],
                "number": 15,
                "repository": "owner/repository",
                "state": "OPEN",
                "status": "verified",
                "worktree_binding": {
                    "base": "main",
                    "branch": "codex/15-bounded-pilot",
                    "role": "direct",
                },
            }
        ),
        encoding="utf-8",
    )
    review = tmp_path / "review.json"
    review.write_text(
        json.dumps({"source_commit": source_commit, "status": "pass", "summary": "reviewed"}),
        encoding="utf-8",
    )
    tests = tmp_path / "tests.json"
    tests.write_text(
        json.dumps({"source_commit": source_commit, "status": "pass", "summary": "tests passed"}),
        encoding="utf-8",
    )
    return {
        "artifact": artifact,
        "health": health,
        "issue": issue,
        "request": request,
        "review": review,
        "rollback": rollback,
        "tests": tests,
        "worktree": worktree,
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
        "--issue-evidence",
        str(inputs["issue"]),
        "--artifact",
        str(inputs["artifact"]),
        "--worktree",
        str(inputs["worktree"]),
        "--review-evidence",
        str(inputs["review"]),
        "--test-evidence",
        str(inputs["tests"]),
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
    assert payload["issue"] == {
        "binding": {
            "base": "main",
            "branch": "codex/15-bounded-pilot",
            "role": "direct",
        },
        "number": 15,
        "repository": "owner/repository",
        "verified": True,
    }
    assert (
        payload["source_commit"]
        == json.loads(inputs["request"].read_text(encoding="utf-8"))["source_commit"]
    )
    assert payload["source"]["isolated_worktree_verified"] is True
    assert payload["review_evidence"]["status"] == "pass"
    assert payload["test_evidence"]["status"] == "pass"
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
        "--issue-evidence",
        str(inputs["issue"]),
        "--artifact",
        str(inputs["artifact"]),
        "--worktree",
        str(inputs["worktree"]),
        "--review-evidence",
        str(inputs["review"]),
        "--test-evidence",
        str(inputs["tests"]),
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


def test_pilot_rejects_a_fabricated_commit_even_when_the_request_claims_isolation(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    inputs = _write_pilot_inputs(tmp_path)
    request = json.loads(inputs["request"].read_text(encoding="utf-8"))
    request["source_commit"] = "0123456789abcdef0123456789abcdef01234567"
    request["worktree_isolated"] = True
    inputs["request"].write_text(json.dumps(request), encoding="utf-8")
    receipt = tmp_path / "deployment-receipt.json"

    result = run_fabric(
        "pilot",
        "--root",
        str(tmp_path),
        "--request",
        str(inputs["request"]),
        "--issue-evidence",
        str(inputs["issue"]),
        "--worktree",
        str(inputs["worktree"]),
        "--artifact",
        str(inputs["artifact"]),
        "--review-evidence",
        str(inputs["review"]),
        "--test-evidence",
        str(inputs["tests"]),
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

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "error": "source commit does not match the selected worktree HEAD",
        "ok": False,
    }
    assert not receipt.exists()


def test_pilot_rejects_failed_health_evidence(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    inputs = _write_pilot_inputs(tmp_path)
    health = json.loads(inputs["health"].read_text(encoding="utf-8"))
    health["status"] = "fail"
    inputs["health"].write_text(json.dumps(health), encoding="utf-8")
    receipt = tmp_path / "deployment-receipt.json"

    result = run_fabric(
        "pilot",
        "--root",
        str(tmp_path),
        "--request",
        str(inputs["request"]),
        "--issue-evidence",
        str(inputs["issue"]),
        "--worktree",
        str(inputs["worktree"]),
        "--artifact",
        str(inputs["artifact"]),
        "--review-evidence",
        str(inputs["review"]),
        "--test-evidence",
        str(inputs["tests"]),
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

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "error": "health evidence must pass for the immutable source commit",
        "ok": False,
    }
    assert not receipt.exists()


def test_pilot_rejects_closed_issue_evidence(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    inputs = _write_pilot_inputs(tmp_path)
    issue = json.loads(inputs["issue"].read_text(encoding="utf-8"))
    issue["state"] = "CLOSED"
    inputs["issue"].write_text(json.dumps(issue), encoding="utf-8")
    receipt = tmp_path / "deployment-receipt.json"

    result = run_fabric(
        "pilot",
        "--root",
        str(tmp_path),
        "--request",
        str(inputs["request"]),
        "--issue-evidence",
        str(inputs["issue"]),
        "--worktree",
        str(inputs["worktree"]),
        "--artifact",
        str(inputs["artifact"]),
        "--review-evidence",
        str(inputs["review"]),
        "--test-evidence",
        str(inputs["tests"]),
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

    assert result.returncode == 1
    assert parse_json_output(result) == {
        "error": "issue evidence does not verify the issue-owned branch",
        "ok": False,
    }
    assert not receipt.exists()


def test_pilot_rejects_unassigned_or_blocked_issue_evidence(
    tmp_path: Path,
    run_fabric: Any,
) -> None:
    for field, value in (("assignees", []), ("blocked_by", [9])):
        case_root = tmp_path / field
        inputs = _write_pilot_inputs(case_root)
        issue = json.loads(inputs["issue"].read_text(encoding="utf-8"))
        issue[field] = value
        inputs["issue"].write_text(json.dumps(issue), encoding="utf-8")
        receipt = case_root / "receipt.json"

        result = run_fabric(
            "pilot",
            "--root",
            str(case_root),
            "--request",
            str(inputs["request"]),
            "--issue-evidence",
            str(inputs["issue"]),
            "--worktree",
            str(inputs["worktree"]),
            "--artifact",
            str(inputs["artifact"]),
            "--review-evidence",
            str(inputs["review"]),
            "--test-evidence",
            str(inputs["tests"]),
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

        assert result.returncode == 1
        assert json.loads(result.stdout)["error"] == (
            "issue evidence does not verify the issue-owned branch"
        )
        assert not receipt.exists()
