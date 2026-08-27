from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fabric_cli.issues import IssueVerifier
from fabric_cli.routing import route_task

ISSUE_BRANCH = re.compile(r"^codex/(?P<issue>\d+)-[a-z0-9][a-z0-9-]*$")
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


def _git(worktree: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(worktree), *arguments],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("selected worktree is not a readable Git worktree")
    return result.stdout.strip()


def _github_repository(value: str) -> str | None:
    patterns = (
        r"^https://github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        r"^git@github\.com:(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
        r"^ssh://git@github\.com/(?P<repo>[^/]+/[^/]+?)(?:\.git)?$",
    )
    for pattern in patterns:
        match = re.fullmatch(pattern, value.strip(), re.IGNORECASE)
        if match is not None:
            return match.group("repo").removesuffix(".git").casefold()
    return None


def _verify_worktree(
    worktree: Path,
    issue_branch: str,
    source_commit: str,
    issue_repository: str,
) -> dict[str, Any]:
    if _git(worktree, "rev-parse", "--is-inside-work-tree") != "true":
        raise ValueError("selected path is not a Git worktree")
    if _git(worktree, "branch", "--show-current") != issue_branch:
        raise ValueError("issue branch does not match the selected worktree")
    if _git(worktree, "rev-parse", "HEAD") != source_commit:
        raise ValueError("source commit does not match the selected worktree HEAD")
    git_dir = _git(worktree, "rev-parse", "--git-dir").replace("\\", "/")
    if "/worktrees/" not in f"/{git_dir.strip('/')}/":
        raise ValueError("pilot requires a registered linked Git worktree")
    if _git(worktree, "status", "--porcelain"):
        raise ValueError("pilot worktree must be clean")
    remote_repository = _github_repository(_git(worktree, "remote", "get-url", "origin"))
    if remote_repository != issue_repository.casefold():
        raise ValueError("worktree origin does not match the verified issue repository")
    return {"isolated_worktree_verified": True}


def _passed_evidence(path: Path, source_commit: str, label: str) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{label} evidence must contain an object")
    if value.get("status") != "pass" or value.get("source_commit") != source_commit:
        raise ValueError(f"{label} evidence must pass for the immutable source commit")
    return {**_digest(path), "status": "pass"}


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
    worktree_path: Path,
    artifact_path: Path,
    review_path: Path,
    test_path: Path,
    health_path: Path,
    rollback_path: Path,
    deployment_authorized: bool,
    issue_verifier: IssueVerifier,
    adapter: RecordOnlyDeploymentAdapter,
) -> dict[str, Any]:
    if not deployment_authorized:
        raise ValueError("explicit deployment authority is required")

    request = _load_request(request_path)
    issue_branch = request.get("issue_branch")
    source_commit = request.get("source_commit")
    branch_match = ISSUE_BRANCH.fullmatch(issue_branch) if isinstance(issue_branch, str) else None
    if branch_match is None:
        raise ValueError("pilot requires an issue-owned branch")
    assert isinstance(issue_branch, str)
    if not isinstance(source_commit, str) or not COMMIT_SHA.fullmatch(source_commit):
        raise ValueError("pilot requires an immutable source commit")
    issue = issue_verifier.verify(int(branch_match.group("issue")), issue_branch)
    issue_repository = issue.get("repository")
    if not isinstance(issue_repository, str):
        raise ValueError("issue verification did not identify a repository")
    source = _verify_worktree(worktree_path, issue_branch, source_commit, issue_repository)

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
    review = _passed_evidence(review_path, source_commit, "review")
    tests = _passed_evidence(test_path, source_commit, "test")
    health = _passed_evidence(health_path, source_commit, "health")
    rollback = _passed_evidence(rollback_path, source_commit, "rollback")
    payload: dict[str, Any] = {
        "artifact": artifact,
        "deployment": {
            "adapter": "record-only",
            "authorized": True,
            "health_evidence": health,
            "rollback_evidence": rollback,
        },
        "issue_branch": issue_branch,
        "issue": issue,
        "ok": True,
        "review_evidence": review,
        "source": source,
        "source_commit": source_commit,
        "test_evidence": tests,
        "worker": worker,
    }
    adapter.record(payload)
    return payload
