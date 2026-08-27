from __future__ import annotations

import json
import os
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
    task_label: node:compute-01
    hardware:
      cpu:
        architecture: x86_64
        evidence: {status: verified, lifetime: chassis}
    admission_gates: [hardware-verified]
""",
        encoding="utf-8",
    )
    (inventory / "repositories.yaml").write_text(
        """\
schema: heterogeneous-compute-fabric/repositories-v1
repositories:
  - repo_id: sample
    supported_architectures: [x86_64]
    required_roles: [cpu-build]
    eligible_nodes: [compute-01]
""",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "[Nodes](inventory/nodes.yaml)\n![Fabric](docs/diagrams/fabric.png)\n",
        encoding="utf-8",
    )
    (diagrams / "fabric.mmd").write_text("flowchart LR\nA-->B\n", encoding="utf-8")
    (diagrams / "fabric.svg").write_text("<svg></svg>\n", encoding="utf-8")
    (diagrams / "fabric.png").write_bytes(b"not-empty")


def parse_json_output(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return json.loads(result.stdout)
