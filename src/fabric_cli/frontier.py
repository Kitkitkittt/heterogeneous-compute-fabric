from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

import yaml

TRIAGE_ACTORS = {
    "needs-triage": "maintainer",
    "needs-info": "reporter-or-operator",
    "ready-for-agent": "agent",
    "ready-for-human": "human",
    "wontfix": "none",
}


class IssueSource(Protocol):
    def load(self) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class FileIssueSource:
    path: Path

    def load(self) -> list[dict[str, Any]]:
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
            raise ValueError("issues file must contain a list of issue objects")
        return value


@dataclass(frozen=True)
class GithubIssueSource:
    repository: str

    def _run_json(self, arguments: list[str]) -> Any:
        result = subprocess.run(
            ["gh", *arguments],
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise ValueError("GitHub issue query failed")
        return json.loads(result.stdout)

    def load(self) -> list[dict[str, Any]]:
        values = self._run_json(
            [
                "issue",
                "list",
                "--repo",
                self.repository,
                "--state",
                "open",
                "--limit",
                "100",
                "--json",
                "number,title,state,labels,assignees",
            ]
        )
        if not isinstance(values, list):
            raise ValueError("GitHub issue query returned an invalid response")
        for value in values:
            if not isinstance(value, dict) or not isinstance(value.get("number"), int):
                raise ValueError("GitHub issue query returned an invalid issue")
            details = self._run_json(
                [
                    "api",
                    f"repos/{self.repository}/issues/{value['number']}",
                ]
            )
            if isinstance(details, dict):
                value["issue_dependencies_summary"] = details.get(
                    "issue_dependencies_summary", {"blocked_by": 0}
                )
        return values


@dataclass(frozen=True)
class NodeConflict:
    node_id: str
    admission_state: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class FrontierIssue:
    number: int
    title: str
    next_actor: str
    suitable_nodes: tuple[str, ...]
    node_conflicts: tuple[NodeConflict, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "next_actor": self.next_actor,
            "node_conflicts": [conflict.as_dict() for conflict in self.node_conflicts],
            "number": self.number,
            "suitable_nodes": list(self.suitable_nodes),
            "title": self.title,
        }


@dataclass(frozen=True)
class FrontierReport:
    frontier: tuple[FrontierIssue, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"frontier": [issue.as_dict() for issue in self.frontier], "ok": True}


def _label_names(value: dict[str, Any]) -> tuple[str, ...]:
    labels = value.get("labels", [])
    return tuple(
        label["name"] if isinstance(label, dict) else label
        for label in labels
        if (isinstance(label, str) and label)
        or (isinstance(label, dict) and isinstance(label.get("name"), str))
    )


def _node_states(root: Path) -> dict[str, str]:
    with (root / "inventory" / "nodes.yaml").open(encoding="utf-8") as handle:
        document = yaml.safe_load(handle)
    if not isinstance(document, dict):
        raise ValueError("nodes registry must contain a mapping")
    return {
        node["node_id"]: node["admission_state"]
        for node in document.get("nodes", [])
        if isinstance(node, dict)
        and isinstance(node.get("node_id"), str)
        and isinstance(node.get("admission_state"), str)
    }


def build_frontier(root: Path, source: IssueSource) -> FrontierReport:
    node_states = _node_states(root)
    frontier: list[FrontierIssue] = []
    for value in source.load():
        if str(value.get("state", "")).upper() != "OPEN":
            continue
        if value.get("assignees"):
            continue
        dependencies = value.get("issue_dependencies_summary", {})
        if isinstance(dependencies, dict) and dependencies.get("blocked_by", 0) > 0:
            continue
        if "pull_request" in value:
            continue

        labels = _label_names(value)
        if "wontfix" in labels:
            continue
        triage = [label for label in labels if label in TRIAGE_ACTORS]
        next_actor = TRIAGE_ACTORS[triage[0]] if len(triage) == 1 else "untriaged"
        suitable_nodes = tuple(
            sorted(label.removeprefix("node:") for label in labels if label.startswith("node:"))
        )
        conflicts = tuple(
            NodeConflict(node_id, node_states.get(node_id, "unknown"))
            for node_id in suitable_nodes
            if node_states.get(node_id) != "schedulable"
        )
        number = value.get("number")
        title = value.get("title")
        if not isinstance(number, int) or not isinstance(title, str):
            raise ValueError("issue is missing a number or title")
        frontier.append(FrontierIssue(number, title, next_actor, suitable_nodes, conflicts))

    return FrontierReport(tuple(sorted(frontier, key=lambda issue: issue.number)))
