# Heterogeneous Compute Fabric

A public-safe source of truth for a small compute fabric that can grow from four nodes into multiple development, compute, cloud, deployment, storage, and gateway nodes.

The fabric distributes **jobs and artifacts**. It does not combine heterogeneous hardware into one virtual computer or split one model across every device.

![Logical compute fabric](docs/diagrams/current-fabric.png)

## Node registry

| Stable node ID | Purpose | Durable capacity | OS policy | Admission state |
| --- | --- | --- | --- | --- |
| `dev-01` | Interactive development and control | Ryzen 7 7840S, 32 GiB, Radeon 780M, 1 TB NVMe | Ubuntu 24.04 LTS; Pop!_OS 24.04 is a supported workstation exception | `install_pending` |
| `compute-01` | CPU/RAM builds, CUDA, inference, batch work | Core i5-12400F, 48 GB, RTX 4060 Ti 16 GB, 500 GB SSD + 2 TB disk | Ubuntu 24.04 LTS, headless-first | `install_pending` |
| `cloud-01` | Bounded ARM64 builds, agents, and auxiliary services | OCI A1 Flex, 4 ARM OCPUs, 24 GB, 50 GB-class boot volume | Existing Linux installation | `verified`, gated |
| `deploy-01` | Persistent services, databases, staging, and storage | Core i5-6300HQ, 23 GiB visible, GTX 960M 2 GB, NVMe + USB SSD/HDD | Existing Ubuntu installation | `verified`, gated |

Admission is fail-closed. A node is not schedulable merely because it boots or answers SSH.

## Start here

- [Domain language](CONTEXT.md)
- [Architecture and workload routing](docs/architecture.md)
- [Machine-readable node registry](inventory/nodes.yaml)
- [Repository registry](inventory/repositories.yaml)
- [Reinstall and admission runbook](docs/runbooks/reinstall-and-admit-node.md)
- [GitHub task routing and node labels](docs/task-routing.md)
- [Fabric CLI reference](docs/cli.md)
- [Public/private operations boundary](docs/runbooks/private-operations-overlay.md)
- [Sanitized audit evidence](docs/audits/2026-08-27-four-node-audit.md)
- [Linux baseline research](docs/research/linux-baseline-options.md)
- [Current operator handoff](handoff.md)

Detailed public hardware records:

- [`dev-01`](inventory/dev-01.md)
- [`compute-01`](inventory/compute-01.md)
- [`cloud-01`](inventory/cloud-01.md)
- [`deploy-01`](inventory/deploy-01.md)

## Operating rules

1. Use stable node IDs in issues, labels, documentation, and evidence. Hostnames are replaceable installation details.
2. Keep hostnames, addresses, SSH users, owners, service inventory, live utilization, and recovery locations in a private operations overlay.
3. Record evidence per field as `verified`, `inherited`, or `unknown`, with a lifetime of `chassis`, `installation`, or `snapshot`.
4. Use Git commits or immutable artifacts between nodes. Never share one writable checkout across agents.
5. Route by declared capabilities and architecture. ARM64, x86_64, CUDA, serving, and storage are separate constraints.
6. Reinstallation and other destructive work requires a `ready-for-human` issue. Post-install verification is a separate `ready-for-agent` issue.

## Next gates

1. Human operator completes [issue #3](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/3): reinstall `compute-01` with Ubuntu 24.04 LTS.
2. An agent completes [issue #4](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/4): verify hardware, private networking/SSH, NVIDIA/CUDA containers, storage, thermals, Git, and an isolated worktree before marking it `schedulable`.
3. Human operator completes [issue #5](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/5): reinstall `dev-01` with Ubuntu 24.04 LTS, or explicitly select the supported Pop!_OS workstation profile.
4. An agent completes [issue #6](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/6): verify the DEV workstation acceptance matrix before admission.
5. Resolve CLOUD cost/ownership/storage gates and DEPLOY ownership/capacity gates before assigning either new work.
6. Run one bounded Git-to-worker-to-deployment pilot before adding a scheduler or cluster framework.

The current files are sanitized. [Issue #7](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/7) separately tracks the owner-authorized rewrite needed to remove superseded identifiers from previously published Git history.

## Fabric CLI

The repository includes a fail-closed command for agents and operators. Install the locked development environment with `uv sync`, then validate a fresh checkout:

```powershell
uv run fabric validate --root .
```

Use `--format json` for automation. An authorized operator may supply a private newline-delimited pattern file with `--prohibited-patterns`; matching values are never repeated in output. The [CLI reference](docs/cli.md) documents routing, overlay, admission, frontier, and pilot commands.

Development checks:

```powershell
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
```
