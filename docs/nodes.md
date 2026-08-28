# Node specifications

These specifications combine reusable node archetypes with public-safe hardware summaries for the current assignments. Hostnames, addresses, users, credentials, API keys, services, access paths, live utilization, and recovery data remain private.

## `dev-01` — Development/control

| Resource | Public specification |
| --- | --- |
| CPU | AMD Ryzen 7 7840S, 8 cores / 16 threads, x86_64 |
| Memory | 32 GiB LPDDR5-6400 |
| Graphics | AMD Radeon 780M integrated GPU with shared system memory |
| Storage | 1 TB NVMe + 500 GB USB disk |
| Primary role | Interactive development, coordination, review, and short feedback loops |

**Responsibilities**

- interactive editing, research, review, and short feedback loops;
- work planning, source-control coordination, and task dispatch;
- lightweight local validation;
- observing results returned by other node roles.

**Exclusions**

- persistent production services;
- default placement for long-running or resource-saturating work;
- authoritative storage for shared artifacts or backups.

**Admission criteria**

- workstation health and recovery checks pass;
- source-control identity and isolated-worktree workflow are verified;
- remote connections use approved private mappings;
- current capacity supports an interactive session.

## `compute-01` — Compute

| Resource | Public specification |
| --- | --- |
| CPU | Intel Core i5-12400F, 6 cores / 12 threads, x86_64 |
| Memory | 48 GB |
| Accelerator | NVIDIA RTX 4060 Ti, 16 GB dedicated VRAM |
| Storage | 500 GB NVMe SSD + 2 TB HDD |
| Primary role | CPU/RAM builds, CUDA, inference, testing, and batch work |

**Responsibilities**

- architecture-compatible builds and test suites;
- memory-intensive data preparation and indexing;
- accelerator workloads when the requested runtime is supported;
- production of immutable artifacts and execution evidence.

**Exclusions**

- assuming accelerator availability from node identity alone;
- persistent services whose continuity conflicts with batch work;
- unbounded jobs without cancellation and capacity controls.

**Admission criteria**

- hardware and installation checks pass for each advertised role;
- storage health, capacity, and thermal behavior are verified;
- accelerator host and container checks pass before accelerator admission;
- execution starts from an isolated checkout or immutable input.

## `cloud-01` — Cloud

| Resource | Public specification |
| --- | --- |
| CPU | ARM64 Neoverse-N1-class allocation, 4 OCPUs |
| Memory | 24 GB |
| Accelerator | None declared |
| Storage | 50 GB-class boot volume |
| Primary role | ARM64 builds, bounded agents, and auxiliary workloads |

**Responsibilities**

- architecture-compatible builds, tests, and bounded agents;
- temporary capacity for workloads that fit the declared cost and data policy;
- auxiliary workloads with explicit ownership and recovery requirements.

**Exclusions**

- assuming virtual allocation proves performance or availability;
- provider-specific identity in public coordination;
- workloads without an owner, budget, or recovery plan.

**Admission criteria**

- architecture and repository compatibility pass;
- private cost, ownership, quota, storage, and recovery gates pass;
- credentials are externally managed and least-privileged;
- teardown and data-retention behavior are defined.

## `deploy-01` — Deployment/data

| Resource | Public specification |
| --- | --- |
| CPU | Intel Core i5-6300HQ, 4 cores / 4 threads, x86_64 |
| Memory | 23 GiB visible |
| Graphics | NVIDIA GTX 960M 2 GB + Intel HD 530 |
| Storage | 512 GB NVMe + 1 TB USB SSD + 4 TB USB HDD |
| Primary role | Persistent services, databases, staging, artifacts, and storage |

**Responsibilities**

- consume reviewed commits or immutable images;
- preserve service and data continuity;
- expose health, backup, restore, and rollback evidence;
- retain owned artifacts according to policy.

**Exclusions**

- interactive development as a normal workload;
- heavy builds, inference, or batch jobs that threaten service continuity;
- deployment from another node's writable working directory.

**Admission criteria**

- service owner and capacity budget are recorded privately;
- backup and sample-restore evidence are current;
- deployment health checks and rollback are verified;
- storage integrity, retention, and recovery gates pass.

## Role composition

A physical or virtual machine may satisfy more than one archetype, but each role is admitted independently. Combining roles is a private deployment decision and must not weaken the stricter role's capacity, isolation, recovery, or security requirements.

## Evaluation status

Hardware totals are nominal inventory. Comparable CPU, memory, storage, GPU, thermal, network, and end-to-end workload benchmarks are **coming soon**.
