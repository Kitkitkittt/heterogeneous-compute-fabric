# Heterogeneous Compute Fabric

A public reference architecture for coordinating heterogeneous development, accelerator, cloud, and service nodes.

The fabric distributes **jobs and immutable artifacts**. It does not merge machines into one virtual computer or split one workload across incompatible devices by default.

![Heterogeneous compute fabric with four public-safe node specifications](docs/diagrams/current-fabric.svg)

## Nominal fleet capacity

| Capacity | Combined inventory | Notes |
| --- | ---: | --- |
| CPU | 18 x86 cores / 32 threads + 4 ARM OCPUs | 22 nominal CPU cores/OCPUs across incompatible architectures |
| Memory | 72 GB + 55 GiB quoted | Mixed vendor-reported GB and OS-reported GiB remain separate; this is not pooled RAM |
| Dedicated GPU memory | 18 GB | RTX 4060 Ti 16 GB + GTX 960M 2 GB; Radeon 780M shared memory excluded |
| Raw storage | ~9.56 TB | NVMe, SSD, HDD, USB, and cloud boot storage before formatting, redundancy, and reservations |
| GPU capability | RTX 4060 Ti + GTX 960M + Radeon 780M | CUDA and integrated-graphics capabilities are separate scheduling lanes |

**Benchmark and evaluation: coming soon.** Planned measurements include per-node CPU, memory, storage, accelerator, thermal, network, and end-to-end workload results. The nominal totals above describe inventory, not guaranteed simultaneous or pooled performance.

## Public scope

This repository contains:

- architectural principles and boundaries;
- public-safe node hardware summaries and role specifications;
- capability-aware workload-routing and lifecycle diagrams;
- shared terminology and architecture decisions.

Implementation code, live operational state, network identities, access procedures, deployment configuration, credentials, API keys, service inventory, recovery data, and private repository locations are intentionally excluded.

## Documentation

- [Architecture](docs/architecture.md)
- [Node specifications](docs/nodes.md)
- [Domain language](CONTEXT.md)
- [Public/private boundary decision](docs/adr/0001-logical-node-identities-and-public-private-split.md)
- [Architecture diagram source](docs/diagrams/current-fabric.architecture.json)
- [Workload-routing diagram source](docs/diagrams/workload-routing.workflow.json)
- [Admission-lifecycle diagram source](docs/diagrams/node-admission.lifecycle.json)

## Core principles

1. Route work by declared capability, not hostname or assumed capacity.
2. Keep logical node identity independent from hardware and operating-system state.
3. Move source through version control and outputs as immutable artifacts.
4. Admit nodes and roles explicitly; connectivity alone never proves readiness.
5. Preserve service continuity by separating interactive, compute, and deployment responsibilities.
6. Keep implementation, access, and operational evidence in access-controlled systems.

## Non-goals

- publishing a deployable cluster implementation;
- documenting hostnames, addresses, users, services, credentials, or access paths;
- aggregating heterogeneous memory or accelerators into one logical device;
- prescribing a scheduler, operating system, network overlay, or model runtime;
- acting as the source of truth for live infrastructure.
