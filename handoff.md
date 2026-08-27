# Operator and agent handoff

Status: documentation and workflow preparation only

The original exploratory handoff has been superseded by the structured source of truth below. It intentionally excludes hostnames, addresses, SSH users, service names, private repository remotes, credential material, and live utilization.

## Read order

1. [Domain language](CONTEXT.md)
2. [Machine-readable nodes](inventory/nodes.yaml)
3. [Architecture](docs/architecture.md)
4. [Reinstall and admission runbook](docs/runbooks/reinstall-and-admit-node.md)
5. [Private overlay contract](docs/runbooks/private-operations-overlay.md)
6. The GitHub issue assigned to the operator or agent

## Current decisions

- Stable public identities use `<purpose>-<ordinal>`.
- `compute-01` and `dev-01` are scheduled for fresh Linux installations by another machine/session.
- Ubuntu 24.04 LTS is the v1 baseline for both nodes.
- Pop!_OS 24.04 is a supported workstation exception for `dev-01`.
- Fedora interoperates with the fabric but is not a supported v1 profile.
- Existing Linux installations on `cloud-01` and `deploy-01` are not part of this reinstall sequence.
- Node targeting uses `node:<node-id>` GitHub labels.
- Human reinstall and agent verification are separate, dependency-linked issues.
- The public repository contains durable capacity and gates. A private overlay contains operational mappings.

## Authority boundary

This documentation task does not authorize:

- reinstalling an operating system;
- changing partitions or deleting data;
- rotating or publishing credentials;
- stopping services or workloads;
- changing cloud resources or billing configuration;
- rewriting published Git history without a separate explicit authorization.

## Immediate execution sequence

1. Complete and merge the sanitized documentation through the existing draft pull request.
2. A human performs [`compute-01` reinstall issue #3](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/3).
3. An agent performs linked [`compute-01` verification issue #4](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/4) and updates evidence.
4. Repeat the human/agent pair through [`dev-01` reinstall issue #5](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/5) and [verification issue #6](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/6).
5. Run a bounded distributed pilot only after both required node capabilities are schedulable.

The acceptance report—not a successful boot—is the authority for changing a node to `schedulable`.

Historical public Git sanitization is tracked separately in [issue #7](https://github.com/Kitkitkittt/heterogeneous-compute-fabric/issues/7). It remains `needs-info`; do not rewrite or force-push history until the owner explicitly authorizes the exact scope and resynchronization plan.
