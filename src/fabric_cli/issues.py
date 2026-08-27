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


def _bound_branch(body: Any) -> str | None:
    if not isinstance(body, str):
        return None
    match = WORKTREE_BINDING.search(body)
    if match is None:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    branch = value.get("branch") if isinstance(value, dict) else None
    return branch if isinstance(branch, str) else None


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
        if (
            self.evidence.get("status") != "verified"
            or self.evidence.get("state") != "OPEN"
            or self.evidence.get("number") != issue_number
            or self.evidence.get("branch") != issue_branch
            or not isinstance(assignees, list)
            or not assignees
            or not all(isinstance(assignee, str) and assignee for assignee in assignees)
            or blocked_by != []
            or not isinstance(repository, str)
            or not repository
        ):
            raise ValueError("issue evidence does not verify the issue-owned branch")
        return {"number": issue_number, "repository": repository, "verified": True}


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
            or not assignees
            or _bound_branch(value.get("body")) != issue_branch
            or open_blockers is None
            or open_blockers
        ):
            raise ValueError("GitHub issue authority does not permit this branch")
        return {"number": issue_number, "repository": self.repository, "verified": True}
