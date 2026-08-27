from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fabric_cli.evidence import is_direct_evidence
from fabric_cli.io import load_mapping


@dataclass(frozen=True)
class NodeDecision:
    node_id: str
    eligible: bool
    reasons: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RouteResult:
    decisions: tuple[NodeDecision, ...]

    @property
    def eligible_nodes(self) -> tuple[str, ...]:
        return tuple(decision.node_id for decision in self.decisions if decision.eligible)

    @property
    def ok(self) -> bool:
        return bool(self.eligible_nodes)

    def as_dict(self) -> dict[str, Any]:
        return {
            "decisions": [decision.as_dict() for decision in self.decisions],
            "eligible_nodes": list(self.eligible_nodes),
            "ok": self.ok,
        }


def _architecture(node: dict[str, Any]) -> str | None:
    hardware = node.get("hardware")
    if not isinstance(hardware, dict):
        return None
    cpu = hardware.get("cpu")
    if not isinstance(cpu, dict):
        return None
    value = cpu.get("architecture")
    return value if isinstance(value, str) else None


def _architecture_evidence(node: dict[str, Any]) -> Any:
    hardware = node.get("hardware")
    cpu = hardware.get("cpu") if isinstance(hardware, dict) else None
    return cpu.get("evidence") if isinstance(cpu, dict) else None


def route_task(
    root: Path,
    repository_id: str,
    architecture: str,
    required_roles: tuple[str, ...],
) -> RouteResult:
    nodes_doc = load_mapping(root / "inventory" / "nodes.yaml")
    repositories_doc = load_mapping(root / "inventory" / "repositories.yaml")

    repositories = repositories_doc.get("repositories", [])
    repository = next(
        (
            value
            for value in repositories
            if isinstance(value, dict) and value.get("repo_id") == repository_id
        ),
        None,
    )
    if repository is None:
        raise ValueError(f"unknown Repository Contract: {repository_id}")

    supported_architectures = repository.get("supported_architectures", [])
    if architecture not in supported_architectures:
        raise ValueError(f"Repository Contract does not support architecture: {architecture}")

    combined_roles = tuple(dict.fromkeys([*repository.get("required_roles", []), *required_roles]))
    candidates = set(repository.get("eligible_nodes", []))
    nodes = {
        node["node_id"]: node
        for node in nodes_doc.get("nodes", [])
        if isinstance(node, dict) and isinstance(node.get("node_id"), str)
    }

    decisions: list[NodeDecision] = []
    for node_id in sorted(candidates):
        node = nodes.get(node_id)
        if node is None:
            decisions.append(NodeDecision(node_id, False, ("unknown Node Slot",)))
            continue

        reasons: list[str] = []
        if node.get("admission_state") != "schedulable":
            reasons.append("node is not schedulable")
        if not is_direct_evidence(node.get("admission_evidence")):
            reasons.append("node admission evidence is not directly verified")
        if _architecture(node) != architecture:
            reasons.append("architecture mismatch")
        elif not is_direct_evidence(_architecture_evidence(node)):
            reasons.append("architecture evidence is not directly verified")

        roles = set(node.get("roles", []))
        role_admission = node.get("role_admission", {})
        role_evidence = node.get("role_admission_evidence", {})
        for role in combined_roles:
            if role not in roles:
                reasons.append(f"missing Role: {role}")
            elif not isinstance(role_admission, dict) or role_admission.get(role) != "schedulable":
                reasons.append(f"Role is not schedulable: {role}")
            elif not isinstance(role_evidence, dict) or not is_direct_evidence(
                role_evidence.get(role)
            ):
                reasons.append(f"Role admission evidence is not directly verified: {role}")

        decisions.append(NodeDecision(node_id, not reasons, tuple(reasons)))

    return RouteResult(tuple(decisions))
