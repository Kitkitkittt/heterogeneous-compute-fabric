from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from fabric_cli.reporting import Check, ValidationReport

ALLOWED_EVIDENCE_STATUSES = {"verified", "inherited", "unknown"}
ALLOWED_EVIDENCE_LIFETIMES = {"chassis", "installation", "snapshot"}
ALLOWED_ADMISSION_STATES = {
    "inventoried",
    "install_pending",
    "installed",
    "verified",
    "schedulable",
    "drained",
    "retired",
}
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".mmd", ".svg", ".json", ".toml", ".py", ".txt"}
IGNORED_PARTS = {".git", ".venv", ".pytest_cache", ".ruff_cache", ".mypy_cache", ".validation"}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
GENERIC_PROHIBITED_PATTERNS = (
    re.compile(r"BEGIN (?:RSA|OPENSSH|EC|DSA) PRIVATE KEY", re.IGNORECASE),
    re.compile(r"\bgh[opsu]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\b(?:100\.(?:6[4-9]|[78][0-9]|9[0-9]|1[01][0-9]|12[0-7]))(?:\.\d{1,3}){2}\b"),
    re.compile(r"[A-Za-z]:\\Users\\[^\\\s]+", re.IGNORECASE),
)


def _load_mapping(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return value


def _walk_evidence(value: Any, location: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        evidence = value.get("evidence")
        if isinstance(evidence, dict):
            status = evidence.get("status")
            lifetime = evidence.get("lifetime")
            if status not in ALLOWED_EVIDENCE_STATUSES:
                errors.append(f"{location}: invalid evidence status")
            if lifetime not in ALLOWED_EVIDENCE_LIFETIMES:
                errors.append(f"{location}: invalid evidence lifetime")
        for key, child in value.items():
            _walk_evidence(child, f"{location}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_evidence(child, f"{location}[{index}]", errors)


def validate_registries(root: Path) -> Check:
    errors: list[str] = []
    try:
        nodes_doc = _load_mapping(root / "inventory" / "nodes.yaml")
        repos_doc = _load_mapping(root / "inventory" / "repositories.yaml")
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return Check("registries", False, (str(exc),))

    if nodes_doc.get("schema") != "heterogeneous-compute-fabric/nodes-v1":
        errors.append("nodes registry has an unsupported schema")
    if repos_doc.get("schema") != "heterogeneous-compute-fabric/repositories-v1":
        errors.append("repositories registry has an unsupported schema")

    nodes = nodes_doc.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes registry must contain at least one Node Slot")
        nodes = []

    node_ids: list[str] = []
    for index, node_value in enumerate(nodes):
        if not isinstance(node_value, dict):
            errors.append(f"nodes[{index}] must be a mapping")
            continue
        node_id = node_value.get("node_id")
        if not isinstance(node_id, str) or not node_id:
            errors.append(f"nodes[{index}] has no node_id")
            continue
        node_ids.append(node_id)
        if node_value.get("task_label") != f"node:{node_id}":
            errors.append(f"{node_id}: task label must match the Node Slot")
        if node_value.get("admission_state") not in ALLOWED_ADMISSION_STATES:
            errors.append(f"{node_id}: invalid Admission State")
        if not node_value.get("roles"):
            errors.append(f"{node_id}: at least one Role is required")
        if not node_value.get("admission_gates"):
            errors.append(f"{node_id}: at least one Admission Gate is required")
        _walk_evidence(node_value.get("hardware", {}), node_id, errors)

    if len(node_ids) != len(set(node_ids)):
        errors.append("Node Slot identifiers must be unique")

    repositories = repos_doc.get("repositories")
    if not isinstance(repositories, list):
        errors.append("repositories must be a list")
        repositories = []
    known_nodes = set(node_ids)
    for index, repository in enumerate(repositories):
        if not isinstance(repository, dict):
            errors.append(f"repositories[{index}] must be a mapping")
            continue
        repo_id = repository.get("repo_id", f"repositories[{index}]")
        eligible = repository.get("eligible_nodes", [])
        if not isinstance(eligible, list):
            errors.append(f"{repo_id}: eligible_nodes must be a list")
            continue
        unknown = sorted(set(eligible) - known_nodes)
        if unknown:
            errors.append(f"{repo_id}: references unknown Node Slots: {', '.join(unknown)}")
        if not repository.get("supported_architectures"):
            errors.append(f"{repo_id}: supported_architectures is required")

    return Check("registries", not errors, tuple(errors))


def _iter_text_files(root: Path) -> list[Path]:
    return [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in TEXT_SUFFIXES
        and not any(part in IGNORED_PARTS for part in path.relative_to(root).parts)
    ]


def validate_links(root: Path) -> Check:
    errors: list[str] = []
    for markdown in root.rglob("*.md"):
        if any(part in IGNORED_PARTS for part in markdown.relative_to(root).parts):
            continue
        try:
            text = markdown.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{markdown.relative_to(root)} is not UTF-8")
            continue
        for target_value in MARKDOWN_LINK.findall(text):
            target = target_value.strip().strip("<>").split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if not (markdown.parent / target).resolve().exists():
                errors.append(f"{markdown.relative_to(root)} has a missing link target")
    return Check("links", not errors, tuple(errors))


def validate_diagrams(root: Path) -> Check:
    errors: list[str] = []
    diagrams_dir = root / "docs" / "diagrams"
    sources = sorted(diagrams_dir.glob("*.mmd")) if diagrams_dir.exists() else []
    if not sources:
        errors.append("no Mermaid diagram sources found")
    for source in sources:
        for suffix in (".svg", ".png"):
            output = source.with_suffix(suffix)
            if not output.is_file() or output.stat().st_size == 0:
                errors.append(f"{source.name} has no non-empty {suffix} output")
    return Check("diagrams", not errors, tuple(errors))


def _literal_patterns(path: Path | None) -> tuple[str, ...]:
    if path is None:
        return ()
    return tuple(
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )


def validate_public_safety(root: Path, prohibited_patterns: Path | None = None) -> Check:
    errors: list[str] = []
    literals = _literal_patterns(prohibited_patterns)
    for path in _iter_text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = path.relative_to(root)
        if any(pattern.search(text) for pattern in GENERIC_PROHIBITED_PATTERNS):
            errors.append(f"{relative}: generic prohibited public pattern matched")
        if any(literal.casefold() in text.casefold() for literal in literals):
            errors.append(f"{relative}: configured prohibited public pattern matched")
    return Check("public-safety", not errors, tuple(errors))


def validate_public_registry(
    root: Path,
    prohibited_patterns: Path | None = None,
) -> ValidationReport:
    return ValidationReport(
        (
            validate_registries(root),
            validate_links(root),
            validate_diagrams(root),
            validate_public_safety(root, prohibited_patterns),
        )
    )
