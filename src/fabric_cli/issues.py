from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


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
        if (
            self.evidence.get("status") != "verified"
            or self.evidence.get("state") != "OPEN"
            or self.evidence.get("number") != issue_number
            or self.evidence.get("branch") != issue_branch
            or not isinstance(repository, str)
            or not repository
        ):
            raise ValueError("issue evidence does not verify the issue-owned branch")
        return {"number": issue_number, "repository": repository, "verified": True}


@dataclass(frozen=True)
class GithubIssueVerifier:
    repository: str

    def verify(self, issue_number: int, issue_branch: str) -> dict[str, Any]:
        del issue_branch
        result = subprocess.run(
            [
                "gh",
                "issue",
                "view",
                str(issue_number),
                "--repo",
                self.repository,
                "--json",
                "number,state,url",
            ],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("GitHub issue verification failed")
        value = json.loads(result.stdout)
        if (
            not isinstance(value, dict)
            or value.get("number") != issue_number
            or value.get("state") != "OPEN"
        ):
            raise ValueError("GitHub issue verification returned the wrong issue")
        return {"number": issue_number, "repository": self.repository, "verified": True}
