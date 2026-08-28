# Heterogeneous Compute Fabric

A public, implementation-neutral reference architecture for coordinating heterogeneous development, accelerator, cloud, and service nodes.

The fabric distributes **jobs and immutable artifacts**. It does not merge machines into one virtual computer or split one workload across incompatible devices by default.

![Conceptual compute fabric](docs/diagrams/current-fabric.svg)

## Public scope

This repository contains only:

- architectural principles and boundaries;
- role-based node specifications;
- conceptual workload-routing and lifecycle diagrams;
- shared terminology and architecture decisions.

Implementation code, real machine inventory, operational state, network identities, access procedures, deployment configuration, credentials, and private repository locations are intentionally excluded.

## Documentation

- [Architecture](docs/architecture.md)
- [Node specifications](docs/nodes.md)
- [Domain language](CONTEXT.md)
- [Public/private boundary decision](docs/adr/0001-logical-node-identities-and-public-private-split.md)
- [Architecture diagram source](docs/diagrams/current-fabric.mmd)
- [Workload-routing diagram source](docs/diagrams/workload-routing.mmd)

## Core principles

1. Route work by declared capability, not hostname or assumed capacity.
2. Keep logical node identity independent from hardware and operating-system state.
3. Move source through version control and outputs as immutable artifacts.
4. Admit nodes and roles explicitly; connectivity alone never proves readiness.
5. Preserve service continuity by separating interactive, compute, and deployment responsibilities.
6. Keep all implementation and operations data in access-controlled systems.

## Non-goals

- publishing a deployable cluster implementation;
- documenting real hosts, cloud resources, services, or access paths;
- aggregating heterogeneous memory or accelerators into one logical device;
- prescribing a scheduler, operating system, network overlay, or model runtime;
- acting as the source of truth for live infrastructure.
