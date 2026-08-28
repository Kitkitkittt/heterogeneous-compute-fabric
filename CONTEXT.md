# Compute Fabric Context

## Purpose

This repository defines a public conceptual model for assigning work to independently managed machines through explicit roles, capabilities, and admission gates.

## Glossary

### Node Slot

A stable logical identity for a capacity role, expressed as `<purpose>-<ordinal>`. A Node Slot survives hostname changes, operating-system reinstalls, and hardware replacement.

### Node Archetype

A reusable specification of responsibilities, required capabilities, exclusions, and admission criteria. An archetype describes a class of nodes, not a real machine.

### Hardware Assignment

The physical machine or virtual allocation privately assigned to a Node Slot. Hardware can change without renaming the slot when its purpose remains stable.

### Installation

The disposable operating-system and software state on a Hardware Assignment. Reinstallation invalidates installation-level evidence.

### Role

A schedulable capability such as interactive development, CPU build, accelerator compute, cloud execution, deployment, or storage.

### Admission State

A fail-closed lifecycle for deciding whether a Node Slot can accept work:

`inventoried -> installation_pending -> installed -> verified -> schedulable`

A schedulable node may move to `drained` for maintenance or incidents and to `retired` when removed.

### Admission Gate

A condition that must pass before a node or role accepts work. Gates cover compatibility, health, capacity, ownership, security, recovery, and rollback as appropriate.

### Capability Contract

The architecture, resources, tools, interfaces, and policy constraints a workload requires and a candidate node declares.

### Immutable Artifact

A content-addressed or versioned output that can move between nodes without sharing a writable working directory.

### Public Concept Repository

This repository. It contains architecture, archetypes, diagrams, terminology, and decisions, but no live infrastructure state or implementation.

### Private Implementation Plane

Access-controlled systems containing source code, machine assignments, operational mappings, configuration, evidence, and runbooks. Secrets remain in an approved credential store rather than source control.

## Invariants

- Public logical identity is independent of private network identity.
- A node accepts work only when its capability contract and admission gates pass.
- Connectivity does not imply authorization, compatibility, capacity, or readiness.
- Source moves through version control; outputs move as immutable artifacts.
- Deployment consumes reviewed, immutable inputs rather than another node's working directory.
- Public documentation never names private repository locations or live infrastructure identifiers.
