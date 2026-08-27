from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

RAW_SECRET_KEYS = {
    "api_key",
    "auth_key",
    "password",
    "private_key",
    "recovery_key",
    "secret",
    "token",
}


@dataclass(frozen=True)
class OverlayNodeSummary:
    node_id: str
    credential_reference_count: int
    status: str = "joined"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OverlayValidationResult:
    nodes: tuple[OverlayNodeSummary, ...]
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "errors": list(self.errors),
            "nodes": [node.as_dict() for node in self.nodes],
            "ok": self.ok,
        }


def _load_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return value


def _contains_raw_secret(value: Any) -> bool:
    if isinstance(value, dict):
        if any(str(key).casefold() in RAW_SECRET_KEYS for key in value):
            return True
        return any(_contains_raw_secret(child) for child in value.values())
    if isinstance(value, list):
        return any(_contains_raw_secret(child) for child in value)
    return False


def validate_overlay(root: Path, overlay_path: Path) -> OverlayValidationResult:
    nodes_doc = _load_mapping(root / "inventory" / "nodes.yaml")
    overlay_doc = _load_mapping(overlay_path)
    if overlay_doc.get("schema") != "heterogeneous-compute-fabric/private-operations-v1":
        return OverlayValidationResult((), ("overlay has an unsupported schema",))

    public_node_ids = {
        node["node_id"]
        for node in nodes_doc.get("nodes", [])
        if isinstance(node, dict) and isinstance(node.get("node_id"), str)
    }
    values = overlay_doc.get("nodes")
    if not isinstance(values, list):
        return OverlayValidationResult((), ("overlay nodes must be a list",))

    seen: set[str] = set()
    summaries: list[OverlayNodeSummary] = []
    errors: list[str] = []
    for index, value in enumerate(values):
        location = f"nodes[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{location}: record must be a mapping")
            continue
        node_id = value.get("node_id")
        raw_secret = _contains_raw_secret(value)
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"{location}: missing node_id")
            if raw_secret:
                errors.append(f"{location}: raw secret field is forbidden")
            continue
        if node_id in seen:
            errors.append(f"{location}: duplicate Node Slot join")
            continue
        seen.add(node_id)
        if node_id not in public_node_ids:
            errors.append(f"{location}: unknown Node Slot")
            continue
        if raw_secret:
            errors.append(f"{location}: raw secret field is forbidden")
            continue

        references = value.get("credential_references")
        if not isinstance(references, list) or not all(
            isinstance(reference, str) and reference for reference in references
        ):
            errors.append(f"{location}: credential references are required")
            continue
        summaries.append(OverlayNodeSummary(node_id, len(references)))

    return OverlayValidationResult(tuple(summaries), tuple(errors))
