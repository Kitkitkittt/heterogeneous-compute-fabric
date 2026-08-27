from __future__ import annotations

from copy import deepcopy
from typing import Any

import pytest

from fabric_cli.issues import FixtureIssueVerifier, GithubIssueVerifier


def _issue(
    branch: str = "codex/21-admission-ci-hardening",
    base: str = "main",
    role: str = "direct",
) -> dict[str, Any]:
    return {
        "assignees": [{"login": "owner"}],
        "body": (
            "## Goal\n\nHarden admission.\n\n### Worktree binding\n\n"
            f'```json\n{{"branch":"{branch}","base":"{base}","role":"{role}"}}\n```'
        ),
        "number": 21,
        "state": "OPEN",
        "url": "https://github.com/owner/repository/issues/21",
    }


def test_live_issue_verifier_requires_assignee_binding_and_no_open_blockers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses: dict[str, Any] = {"issue": _issue(), "blockers": []}

    def fake_json(command: list[str]) -> Any:
        return (
            responses["blockers"]
            if "dependencies/blocked_by" in command[-1]
            else responses["issue"]
        )

    monkeypatch.setattr("fabric_cli.issues._run_json", fake_json)
    verifier = GithubIssueVerifier("owner/repository")

    assert verifier.verify(21, "codex/21-admission-ci-hardening")["verified"] is True

    for mutation in ("assignee", "multiple_assignees", "binding", "base", "role", "blocker"):
        responses["issue"] = _issue()
        responses["blockers"] = []
        if mutation == "assignee":
            responses["issue"]["assignees"] = []
        elif mutation == "multiple_assignees":
            responses["issue"]["assignees"].append({"login": "second-owner"})
        elif mutation == "binding":
            responses["issue"] = _issue("codex/99-wrong-branch")
        elif mutation == "base":
            responses["issue"] = _issue(base="")
        elif mutation == "role":
            responses["issue"] = _issue(role="observer")
        else:
            responses["blockers"] = [{"number": 9, "state": "open"}]

        with pytest.raises(ValueError, match="issue authority"):
            verifier.verify(21, "codex/21-admission-ci-hardening")


def test_fixture_issue_verifier_requires_complete_binding_and_one_assignee() -> None:
    evidence: dict[str, Any] = {
        "assignees": ["owner"],
        "blocked_by": [],
        "number": 21,
        "repository": "owner/repository",
        "state": "OPEN",
        "status": "verified",
        "worktree_binding": {
            "base": "main",
            "branch": "codex/21-admission-ci-hardening",
            "role": "direct",
        },
    }
    assert (
        FixtureIssueVerifier(evidence).verify(
            21,
            "codex/21-admission-ci-hardening",
        )["verified"]
        is True
    )

    for mutation in ("multiple_assignees", "missing_base", "invalid_role"):
        invalid = deepcopy(evidence)
        if mutation == "multiple_assignees":
            invalid["assignees"].append("second-owner")
        elif mutation == "missing_base":
            invalid["worktree_binding"].pop("base")
        else:
            invalid["worktree_binding"]["role"] = "observer"
        with pytest.raises(ValueError, match="issue evidence"):
            FixtureIssueVerifier(invalid).verify(
                21,
                "codex/21-admission-ci-hardening",
            )
