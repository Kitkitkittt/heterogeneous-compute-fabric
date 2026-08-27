from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fabric_cli.routing import route_task

ISSUE_BRANCH = re.compile(r"^codex/\d+-[a-z0-9][a-z0-9-]*$")
COMMIT_SHA = re.compile(r"^[0-9a-f]{40}$")


def _load_request(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("pilot request must contain an object")
    return value


def _digest(path: Path) -> dict[str, Any]:
    value = path.read_bytes()
    if not value:
        raise ValueError(f"{path.name} must not be empty")
    return {"bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()}


@dataclass(frozen=True)
class RecordOnlyDeploymentAdapter:
    receipt_path: Path

    def record(self, payload: dict[str, Any]) -> None:
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.receipt_path.with_suffix(self.receipt_path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(self.receipt_path)


def run_pilot(
    root: Path,
    request_path: Path,
    artifact_path: Path,
    health_path: Path,
    rollback_path: Path,
    deployment_authorized: bool,
    adapter: RecordOnlyDeploymentAdapter,
) -> dict[str, Any]:
    if not deployment_authorized:
        raise ValueError("explicit deployment authority is required")

    request = _load_request(request_path)
    issue_branch = request.get("issue_branch")
    source_commit = request.get("source_commit")
    if not isinstance(issue_branch, str) or not ISSUE_BRANCH.fullmatch(issue_branch):
        raise ValueError("pilot requires an issue-owned branch")
    if request.get("worktree_isolated") is not True:
        raise ValueError("pilot requires an isolated worktree")
    if not isinstance(source_commit, str) or not COMMIT_SHA.fullmatch(source_commit):
        raise ValueError("pilot requires an immutable source commit")

    repository = request.get("repository")
    architecture = request.get("architecture")
    roles = request.get("required_roles")
    if not isinstance(repository, str) or not isinstance(architecture, str):
        raise ValueError("pilot request is missing repository or architecture")
    if not isinstance(roles, list) or not all(isinstance(role, str) for role in roles):
        raise ValueError("pilot required_roles must be a list of Role names")

    route = route_task(root, repository, architecture, tuple(roles))
    if not route.ok:
        raise ValueError("pilot has no eligible admitted worker")
    preferred_node = request.get("preferred_node")
    if preferred_node is not None and preferred_node not in route.eligible_nodes:
        raise ValueError("preferred worker is not eligible")
    worker = preferred_node or route.eligible_nodes[0]

    artifact = _digest(artifact_path)
    health = _digest(health_path)
    rollback = _digest(rollback_path)
    payload: dict[str, Any] = {
        "artifact": artifact,
        "deployment": {
            "adapter": "record-only",
            "authorized": True,
            "health_evidence": health,
            "rollback_evidence": rollback,
        },
        "issue_branch": issue_branch,
        "ok": True,
        "source_commit": source_commit,
        "worker": worker,
    }
    adapter.record(payload)
    return payload
