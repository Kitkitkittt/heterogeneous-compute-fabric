from __future__ import annotations

from typing import Any

import pytest

from fabric_cli.issues import GithubIssueVerifier


def _issue(branch: str = "codex/21-admission-ci-hardening") -> dict[str, Any]:
    return {
        "assignees": [{"login": "owner"}],
        "body": (
            "## Goal\n\nHarden admission.\n\n### Worktree binding\n\n"
            f'```json\n{{"branch":"{branch}","base":"main","role":"direct"}}\n```'
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

    for mutation in ("assignee", "binding", "blocker"):
        responses["issue"] = _issue()
        responses["blockers"] = []
        if mutation == "assignee":
            responses["issue"]["assignees"] = []
        elif mutation == "binding":
            responses["issue"] = _issue("codex/99-wrong-branch")
        else:
            responses["blockers"] = [{"number": 9, "state": "open"}]

        with pytest.raises(ValueError, match="issue authority"):
            verifier.verify(21, "codex/21-admission-ci-hardening")
