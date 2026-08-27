from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

from fabric_cli.evidence import is_direct_evidence
from fabric_cli.io import load_mapping
from fabric_cli.reporting import Check, ValidationReport
from fabric_cli.safety import PUBLIC_PROHIBITED_PATTERNS

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
BINARY_SUFFIXES = {".gif", ".ico", ".jpeg", ".jpg", ".pdf", ".png", ".webp"}
IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".validation",
    ".venv",
    "__pycache__",
    "node_modules",
}
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REPOSITORY_FIELDS = {
    "repo_id",
    "access_class",
    "canonical_remote",
    "purpose",
    "default_branch",
    "supported_architectures",
    "required_roles",
    "eligible_nodes",
    "bootstrap_command",
    "verification_command",
    "deployment_targets",
    "secrets_required",
}
CHECKOUT_POLICY_FIELDS = {
    "source_transport",
    "active_writer",
    "shared_writable_checkout",
    "deployment_input",
}


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


def _require_hardware_evidence(hardware: Any, node_id: str, errors: list[str]) -> None:
    if not isinstance(hardware, dict):
        errors.append(f"{node_id}: hardware must be a mapping")
        return
    for category in ("system", "cpu", "memory", "network_capabilities"):
        value = hardware.get(category)
        if not isinstance(value, dict) or not isinstance(value.get("evidence"), dict):
            errors.append(f"{node_id}: hardware.{category} requires evidence")
    for category in ("accelerators", "storage"):
        values = hardware.get(category, [])
        if not isinstance(values, list):
            errors.append(f"{node_id}: hardware.{category} must be a list")
            continue
        for index, value in enumerate(values):
            if not isinstance(value, dict) or not isinstance(value.get("evidence"), dict):
                errors.append(f"{node_id}: hardware.{category}[{index}] requires evidence")


def validate_registries(root: Path) -> Check:
    errors: list[str] = []
    try:
        nodes_doc = load_mapping(root / "inventory" / "nodes.yaml")
        repos_doc = load_mapping(root / "inventory" / "repositories.yaml")
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
        roles = node_value.get("roles", [])
        role_admission = node_value.get("role_admission")
        if not isinstance(role_admission, dict) or set(role_admission) != set(roles):
            errors.append(f"{node_id}: role_admission must cover every declared Role")
        elif any(state not in ALLOWED_ADMISSION_STATES for state in role_admission.values()):
            errors.append(f"{node_id}: role_admission has an invalid state")
        if not node_value.get("admission_gates"):
            errors.append(f"{node_id}: at least one Admission Gate is required")
        admission_state = node_value.get("admission_state")
        admission_evidence = node_value.get("admission_evidence")
        if admission_state == "schedulable" and not is_direct_evidence(admission_evidence):
            errors.append(
                f"{node_id}: schedulable node requires directly verified admission evidence"
            )
        role_evidence = node_value.get("role_admission_evidence")
        if isinstance(role_admission, dict):
            for role, state in role_admission.items():
                evidence = role_evidence.get(role) if isinstance(role_evidence, dict) else None
                if state == "schedulable" and not is_direct_evidence(evidence):
                    errors.append(
                        f"{node_id}: schedulable Role {role} requires directly verified "
                        "admission evidence"
                    )
        hardware = node_value.get("hardware", {})
        _require_hardware_evidence(hardware, node_id, errors)
        _walk_evidence(hardware, node_id, errors)

    if len(node_ids) != len(set(node_ids)):
        errors.append("Node Slot identifiers must be unique")

    repositories = repos_doc.get("repositories")
    if not isinstance(repositories, list):
        errors.append("repositories must be a list")
        repositories = []
    known_nodes = set(node_ids)
    node_roles = {
        node.get("node_id"): set(node.get("roles", []))
        for node in nodes
        if isinstance(node, dict) and isinstance(node.get("node_id"), str)
    }
    checkout_policy = repos_doc.get("checkout_policy")
    if not isinstance(checkout_policy, dict):
        errors.append("repositories registry requires checkout_policy")
    else:
        for field in sorted(CHECKOUT_POLICY_FIELDS):
            if not checkout_policy.get(field):
                errors.append(f"checkout_policy: {field} is required")
    for index, repository in enumerate(repositories):
        if not isinstance(repository, dict):
            errors.append(f"repositories[{index}] must be a mapping")
            continue
        repo_id = repository.get("repo_id", f"repositories[{index}]")
        for field in sorted(REPOSITORY_FIELDS):
            value = repository.get(field)
            if value is None or value == "":
                errors.append(f"{repo_id}: {field} is required")
        eligible = repository.get("eligible_nodes", [])
        if not isinstance(eligible, list):
            errors.append(f"{repo_id}: eligible_nodes must be a list")
            continue
        unknown = sorted(set(eligible) - known_nodes)
        if unknown:
            errors.append(f"{repo_id}: references unknown Node Slots: {', '.join(unknown)}")
        if not repository.get("supported_architectures"):
            errors.append(f"{repo_id}: supported_architectures is required")
        required_roles = repository.get("required_roles")
        if not isinstance(required_roles, list):
            errors.append(f"{repo_id}: required_roles must be a list")
        else:
            available_roles = set().union(
                *(
                    node_roles.get(node_id, set())
                    for node_id in eligible
                    if isinstance(node_id, str)
                )
            )
            missing_roles = sorted(set(required_roles) - available_roles)
            if missing_roles:
                errors.append(
                    f"{repo_id}: required Roles have no eligible Node Slot: "
                    f"{', '.join(missing_roles)}"
                )
        deployment_targets = repository.get("deployment_targets")
        if not isinstance(deployment_targets, list):
            errors.append(f"{repo_id}: deployment_targets must be a list")
        elif sorted(set(deployment_targets) - known_nodes):
            errors.append(f"{repo_id}: deployment_targets reference unknown Node Slots")
        for field in ("secrets_required",):
            value = repository.get(field)
            if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
                errors.append(f"{repo_id}: {field} must be a list of names")

    return Check("registries", not errors, tuple(errors))


def _iter_text_files(root: Path) -> list[Path]:
    return [path for path in _iter_files(root) if path.suffix.lower() not in BINARY_SUFFIXES]


def _iter_files(root: Path) -> list[Path]:
    paths: list[Path] = []
    for directory, names, files in os.walk(root):
        names[:] = [name for name in names if name not in IGNORED_PARTS]
        paths.extend(Path(directory) / name for name in files)
    return paths


def validate_links(root: Path) -> Check:
    errors: list[str] = []
    for markdown in (path for path in _iter_files(root) if path.suffix.lower() == ".md"):
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
    manifest_path = diagrams_dir / "render-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        manifest = None
        errors.append("diagram render manifest is missing or invalid")
    manifest_sources = manifest.get("sources") if isinstance(manifest, dict) else None
    if isinstance(manifest, dict) and (
        manifest.get("schema") != "heterogeneous-compute-fabric/diagram-render-manifest-v1"
        or manifest.get("renderer") != "@mermaid-js/mermaid-cli@11.16.0"
    ):
        errors.append("diagram render manifest has an unsupported contract")
    if not isinstance(manifest_sources, dict):
        manifest_sources = {}
    if set(manifest_sources) != {source.name for source in sources}:
        errors.append("diagram render manifest does not cover every Mermaid source")
    renderer = _mermaid_command(root)
    if renderer is None:
        errors.append("pinned Mermaid renderer is unavailable; run npm ci")
    for source in sources:
        text = source.read_text(encoding="utf-8")
        if not re.search(
            r"(?m)^(?:flowchart|graph|sequenceDiagram|stateDiagram|classDiagram)\b", text
        ):
            errors.append(f"{source.name} has no supported Mermaid diagram declaration")
        manifest_entry = manifest_sources.get(source.name)
        if not _manifest_matches(source, manifest_entry):
            errors.append(f"{source.name} does not match the render manifest")
        if renderer is not None and not _mermaid_renders(renderer, source):
            errors.append(f"{source.name} does not render with the pinned Mermaid CLI")
        for suffix in (".svg", ".png"):
            output = source.with_suffix(suffix)
            if not output.is_file() or output.stat().st_size == 0:
                errors.append(f"{source.name} has no non-empty {suffix} output")
                continue
            try:
                width, height = _diagram_dimensions(output)
            except (OSError, ValueError, ET.ParseError, struct.error):
                errors.append(f"{source.name} has an invalid {suffix} output")
                continue
            if width < 600 or height < 600:
                errors.append(f"{source.name} has an illegible {suffix} output")
    return Check("diagrams", not errors, tuple(errors))


def _manifest_matches(source: Path, value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    artifacts = {
        "source_sha256": source,
        "svg_sha256": source.with_suffix(".svg"),
        "png_sha256": source.with_suffix(".png"),
    }
    return all(
        path.is_file() and value.get(field) == hashlib.sha256(path.read_bytes()).hexdigest()
        for field, path in artifacts.items()
    )


def _mermaid_command(root: Path) -> tuple[str, ...] | None:
    node = shutil.which("node")
    if node is None:
        return None
    package_root = Path(__file__).resolve().parents[2]
    for candidate_root in (root, package_root):
        script = candidate_root / "node_modules" / "@mermaid-js" / "mermaid-cli" / "src" / "cli.js"
        if script.is_file():
            return node, str(script)
    return None


def _mermaid_renders(command: tuple[str, ...], source: Path) -> bool:
    with tempfile.TemporaryDirectory(prefix="fabric-mermaid-") as temporary:
        output = Path(temporary) / "rendered.svg"
        try:
            result = subprocess.run(
                [*command, "-i", str(source), "-o", str(output), "-b", "transparent"],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
                timeout=45,
            )
        except (OSError, subprocess.TimeoutExpired):
            return False
        return result.returncode == 0 and output.is_file() and output.stat().st_size > 0


def _diagram_dimensions(path: Path) -> tuple[float, float]:
    if path.suffix == ".png":
        value = path.read_bytes()[:24]
        if len(value) < 24 or value[:8] != b"\x89PNG\r\n\x1a\n" or value[12:16] != b"IHDR":
            raise ValueError("invalid PNG header")
        width, height = struct.unpack(">II", value[16:24])
        return float(width), float(height)
    root = ET.parse(path).getroot()
    view_box = root.attrib.get("viewBox", "").split()
    if len(view_box) == 4:
        return float(view_box[2]), float(view_box[3])
    return _svg_number(root.attrib.get("width")), _svg_number(root.attrib.get("height"))


def _svg_number(value: str | None) -> float:
    if value is None:
        raise ValueError("SVG dimension is missing")
    match = re.match(r"[0-9.]+", value)
    if match is None:
        raise ValueError("SVG dimension is invalid")
    return float(match.group())


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
        if any(pattern.search(text) for pattern in PUBLIC_PROHIBITED_PATTERNS):
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
