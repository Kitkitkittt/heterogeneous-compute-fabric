from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

WORKTREE_BINDING = re.compile(
    r"### Worktree binding\s*```json\s*(\{.*?\})\s*```",
    re.DOTALL,
)
VALID_BINDING_ROLES = {"direct", "integration", "leaf"}


@dataclass(frozen=True)
class WorktreeBinding:
    branch: str
    base: str
    role: str

    @classmethod
    def from_value(cls, value: Any) -> WorktreeBinding | None:
        if not isinstance(value, dict):
            return None
        branch = value.get("branch")
        base = value.get("base")
        role = value.get("role")
        if (
            not isinstance(branch, str)
            or not branch
            or not isinstance(base, str)
            or not base
            or role not in VALID_BINDING_ROLES
        ):
            return None
        return cls(branch, base, role)


def _run_json(command: list[str]) -> Any:
    result = subprocess.run(
        command,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError("GitHub issue verification failed")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("GitHub issue verification returned invalid JSON") from exc


def _worktree_binding(body: Any) -> WorktreeBinding | None:
    if not isinstance(body, str):
        return None
    match = WORKTREE_BINDING.search(body)
    if match is None:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return WorktreeBinding.from_value(value)


class IssueVerifier(Protocol):
    def verify(self, issue_number: int, issue_branch: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class FixtureIssueVerifier:
    evidence: dict[str, Any]

    @classmethod
    def from_path(cls, path: Path) -> FixtureIssueVerifier:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError("issue evidence must contain an object")
        return cls(value)

    def verify(self, issue_number: int, issue_branch: str) -> dict[str, Any]:
        repository = self.evidence.get("repository")
        assignees = self.evidence.get("assignees")
        blocked_by = self.evidence.get("blocked_by")
        binding = WorktreeBinding.from_value(self.evidence.get("worktree_binding"))
        if (
            self.evidence.get("status") != "verified"
            or self.evidence.get("state") != "OPEN"
            or self.evidence.get("number") != issue_number
            or binding is None
            or binding.branch != issue_branch
            or not isinstance(assignees, list)
            or len(assignees) != 1
            or not all(isinstance(assignee, str) and assignee for assignee in assignees)
            or blocked_by != []
            or not isinstance(repository, str)
            or not repository
        ):
            raise ValueError("issue evidence does not verify the issue-owned branch")
        return {
            "binding": binding.__dict__,
            "number": issue_number,
            "repository": repository,
            "verified": True,
        }


@dataclass(frozen=True)
class GithubIssueVerifier:
    repository: str

    def verify(self, issue_number: int, issue_branch: str) -> dict[str, Any]:
        value = _run_json(
            [
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--repo",
                self.repository,
                "--json",
                "number,state,url,assignees,body",
            ],
        )
        blockers = _run_json(
            [
                "gh",
                "api",
                f"repos/{self.repository}/issues/{issue_number}/dependencies/blocked_by",
            ]
        )
        assignees = value.get("assignees") if isinstance(value, dict) else None
        binding = _worktree_binding(value.get("body")) if isinstance(value, dict) else None
        open_blockers = (
            [blocker for blocker in blockers if blocker.get("state", "").casefold() == "open"]
            if isinstance(blockers, list) and all(isinstance(blocker, dict) for blocker in blockers)
            else None
        )
        if (
            not isinstance(value, dict)
            or value.get("number") != issue_number
            or value.get("state") != "OPEN"
            or not isinstance(assignees, list)
            or len(assignees) != 1
            or not isinstance(assignees[0], dict)
            or not isinstance(assignees[0].get("login"), str)
            or not assignees[0]["login"]
            or binding is None
            or binding.branch != issue_branch
            or open_blockers is None
            or open_blockers
        ):
            raise ValueError("GitHub issue authority does not permit this branch")
        return {
            "binding": binding.__dict__,
            "number": issue_number,
            "repository": self.repository,
            "verified": True,
        }
