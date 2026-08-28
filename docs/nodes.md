# Node specifications

These specifications define public node archetypes. They intentionally omit real hardware, software versions, admission state, ownership, and access data.

## Development/control node

**Logical series:** `dev-N`

**Purpose:** Provide the human-facing workspace and coordination point for the fabric.

**Responsibilities**

- interactive editing, research, review, and short feedback loops;
- work planning, source-control coordination, and task dispatch;
- lightweight local validation;
- observing results returned by other node roles.

**Capability contract**

- responsive interactive environment;
- source-control and secure remote-execution clients;
- enough local capacity for coordination and bounded tests;
- access to approved external or local inference endpoints when required.

**Exclusions**

- persistent production services;
- default placement for long-running or resource-saturating work;
- authoritative storage for shared artifacts or backups.

**Admission criteria**

- workstation health and recovery checks pass;
- source-control identity and isolated-worktree workflow are verified;
- remote connections use approved private mappings;
- current capacity supports an interactive session.

## Compute node

**Logical series:** `compute-N`

**Purpose:** Execute bounded CPU, memory, accelerator, build, test, inference, and batch workloads.

**Responsibilities**

- architecture-compatible builds and test suites;
- memory-intensive data preparation and indexing;
- accelerator workloads when the requested runtime is supported;
- production of immutable artifacts and execution evidence.

**Capability contract**

- declared CPU architecture and resource envelope;
- optional accelerator described as an independent capability lane;
- reproducible execution environment;
- bounded resource use, health reporting, and artifact output.

**Exclusions**

- assuming accelerator availability from node identity alone;
- persistent services whose continuity conflicts with batch work;
- unbounded jobs without cancellation and capacity controls.

**Admission criteria**

- hardware and installation checks pass for each advertised role;
- storage health, capacity, and thermal behavior are verified;
- accelerator host and container checks pass before accelerator admission;
- execution starts from an isolated checkout or immutable input.

## Cloud node

**Logical series:** `cloud-N`

**Purpose:** Supply remote, elastic, or architecture-specific capacity without coupling workflows to a provider.

**Responsibilities**

- architecture-compatible builds, tests, and bounded agents;
- temporary capacity for workloads that fit the declared cost and data policy;
- auxiliary services with explicit ownership and recovery requirements.

**Capability contract**

- declared processor architecture and resource allocation;
- explicit cost, quota, region, and data-handling policy in private records;
- reproducible bootstrap and teardown path;
- immutable input and output exchange.

**Exclusions**

- assuming virtual allocation proves performance or availability;
- provider-specific identity in public coordination;
- workloads without an owner, budget, or recovery plan.

**Admission criteria**

- architecture and repository compatibility pass;
- private cost, ownership, quota, storage, and recovery gates pass;
- credentials are externally managed and least-privileged;
- teardown and data-retention behavior are defined.

## Deployment/data node

**Logical series:** `deploy-N`

**Purpose:** Host persistent services, staging workloads, databases, storage, and deployment health checks.

**Responsibilities**

- consume reviewed commits or immutable images;
- preserve service and data continuity;
- expose health, backup, restore, and rollback evidence;
- retain owned artifacts according to policy.

**Capability contract**

- stable service runtime and durable storage roles;
- explicit resource budgets and workload ownership;
- backup, restore, retention, and rollback procedures;
- isolation between serving workloads and maintenance work.

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
