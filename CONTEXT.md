# Compute Fabric Context

## Purpose

This repository describes how independently managed machines accept development, compute, cloud, deployment, and storage work through explicit capability and admission contracts.

## Glossary

### Node Slot

A stable logical identity such as `compute-01`. A Node Slot survives hostname changes, operating-system reinstalls, and hardware replacement. Use this term and ID in public documentation, issues, and task labels.

Avoid using a hostname as the identity of a node.

### Hardware Assignment

The physical machine or virtual-machine allocation currently assigned to a Node Slot. Hardware may be swapped without renaming the slot when its purpose remains the same.

### Installation

The disposable operating-system state on a Hardware Assignment. It includes the OS profile, packages, drivers, host keys, Tailscale registration, and local configuration. A reinstall invalidates installation evidence.

### OS Profile

A versioned bootstrap and acceptance contract, such as `ubuntu24` or `pop24`. Sharing protocols does not make different profiles operationally identical.

### Role

A schedulable capability such as `interactive-development`, `cpu-build`, `cuda`, `arm64-build`, `deployment`, or `storage`. Roles are labels on a Node Slot, not permanent claims about a machine.

### Role Profile

A reusable admission-check bundle such as `compute` or `workstation`. It maps observed checks to Roles but does not identify a Node Slot or an operating system. For example, `compute-02` can reuse the `compute` Role Profile while selecting the `ubuntu24` OS Profile.

### Admission State

The fail-closed lifecycle of a Node Slot:

`inventoried -> install_pending -> installed -> verified -> schedulable`

`drained` and `retired` are terminal operating states. A node may be `verified` but still gated from scheduling.

### Admission Gate

A check that must pass before a node or capability can be scheduled. Examples include backup evidence, key-based access, disk health, CUDA container verification, workload ownership, and cost status.

### Evidence Status

- `verified`: observed directly by an identified audit method.
- `inherited`: copied from prior documentation and not reverified in the current audit.
- `unknown`: not safely established.

### Evidence Lifetime

- `chassis`: remains valid across reinstall, but not a hardware swap.
- `installation`: invalidated by OS reinstall or material configuration change.
- `snapshot`: live load, free capacity, services, and similar rapidly stale observations.

### Public Registry

The sanitized, version-controlled node and repository contracts in this repository. It contains logical IDs, durable capacity, evidence state, roles, and gates.

### Private Operations Overlay

A separately access-controlled mapping from Node Slots to current hostnames, addresses, SSH users, owners, service inventory, recovery locations, and credential references. Secrets themselves stay in a credential store.

### Repository Contract

A machine-readable declaration of a repository's architecture support, capability requirements, eligible nodes, checkout policy, bootstrap command, and verification command.

## Invariants

- Public Node Slot identity is independent of private network identity.
- No Node Slot or Role becomes schedulable without directly verified, dated admission evidence and a public-safe source reference.
- Human-authorized destructive work and agent verification are separate issues.
- Source moves through Git; outputs move as immutable artifacts.
- Task suitability may name multiple Node Slots through `node:<node-id>` labels.

