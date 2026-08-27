from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def run_fabric() -> Any:
    def run(*args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        return subprocess.run(
            [sys.executable, "-m", "fabric_cli", *args],
            cwd=PROJECT_ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    return run


def write_valid_registry(root: Path) -> None:
    inventory = root / "inventory"
    diagrams = root / "docs" / "diagrams"
    inventory.mkdir(parents=True)
    diagrams.mkdir(parents=True)
    for relative in (
        "AGENTS.md",
        ".agents/skills/fabric-collaboration/SKILL.md",
        "docs/agents/collaboration.md",
        "docs/agents/domain.md",
        "docs/agents/issue-tracker.md",
        "docs/agents/triage-labels.md",
    ):
        contract = root / relative
        contract.parent.mkdir(parents=True, exist_ok=True)
        contract.write_text("# Test agent contract\n", encoding="utf-8")

    (inventory / "nodes.yaml").write_text(
        """\
schema: heterogeneous-compute-fabric/nodes-v1
evidence_contract:
  statuses: [verified, inherited, unknown]
  lifetimes: [chassis, installation, snapshot]
  admission_states:
    [inventoried, install_pending, installed, verified, schedulable, drained, retired]
nodes:
  - node_id: compute-01
    admission_state: schedulable
    roles: [cpu-build]
    role_admission: {cpu-build: schedulable}
    admission_evidence:
      status: verified
      observed_at: 2026-08-27
      source: acceptance-report
    role_admission_evidence:
      cpu-build: {status: verified, observed_at: 2026-08-27, source: acceptance-report}
    task_label: node:compute-01
    hardware:
      system:
        model: test-system
        evidence: {status: verified, lifetime: chassis}
      cpu:
        architecture: x86_64
        evidence:
          {status: verified, lifetime: chassis, observed_at: 2026-08-27,
           source: hardware-audit}
      memory:
        installed_gb: 48
        evidence: {status: verified, lifetime: chassis}
      network_capabilities:
        values: [private-overlay]
        evidence: {status: verified, lifetime: installation}
    admission_gates: [hardware-verified]
""",
        encoding="utf-8",
    )
    (inventory / "repositories.yaml").write_text(
        """\
schema: heterogeneous-compute-fabric/repositories-v1
checkout_policy:
  source_transport: git
  active_writer: one issue-owned branch in one isolated worktree
  shared_writable_checkout: forbidden
  deployment_input: immutable commit or image
repositories:
  - repo_id: sample
    access_class: public
    canonical_remote: https://github.com/owner/repository
    purpose: behavioral-test fixture
    default_branch: main
    supported_architectures: [x86_64]
    required_roles: [cpu-build]
    eligible_nodes: [compute-01]
    bootstrap_command: uv sync
    verification_command: uv run fabric validate --root .
    deployment_targets: []
    secrets_required: []
""",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "[Nodes](inventory/nodes.yaml)\n![Fabric](docs/diagrams/fabric.png)\n",
        encoding="utf-8",
    )
    mermaid = "flowchart LR\nA-->B\n"
    (diagrams / "fabric.mmd").write_text(mermaid, encoding="utf-8")
    (diagrams / "fabric.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="800" '
        'viewBox="0 0 1200 800"><text>A to B</text></svg>\n',
        encoding="utf-8",
    )
    (diagrams / "fabric.png").write_bytes(
        b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\rIHDR" + struct.pack(">II", 1200, 800)
    )
    (diagrams / "render-manifest.json").write_text(
        json.dumps(
            {
                "renderer": "@mermaid-js/mermaid-cli@11.16.0",
                "schema": "heterogeneous-compute-fabric/diagram-render-manifest-v1",
                "sources": {
                    "fabric.mmd": {
                        "png_sha256": hashlib.sha256(
                            (diagrams / "fabric.png").read_bytes()
                        ).hexdigest(),
                        "source_sha256": hashlib.sha256(
                            (diagrams / "fabric.mmd")
                            .read_bytes()
                            .replace(b"\r\n", b"\n")
                            .replace(b"\r", b"\n")
                        ).hexdigest(),
                        "svg_sha256": hashlib.sha256(
                            (diagrams / "fabric.svg").read_bytes()
                        ).hexdigest(),
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def append_node(root: Path, node_yaml: str) -> None:
    nodes_path = root / "inventory" / "nodes.yaml"
    nodes_path.write_text(
        nodes_path.read_text(encoding="utf-8") + node_yaml,
        encoding="utf-8",
    )


def parse_json_output(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    value = json.loads(result.stdout)
    assert isinstance(value, dict)
    return value
