# Current architecture and workload routing

This document turns the initial concept into an operating model that reflects the 2026-08-27 read-only audit.

## The three roles

### DEV — control and interactive work

`KeithVo` remains the human-facing control node. It owns planning, browser work, Git coordination, primary editing, and short feedback loops. It should not become the persistent database or local-model server.

### COMPUTE — CPU, RAM, and GPU work

`desktop-x2w7f` is not merely a GPU appliance. Treat it as three capacity lanes behind one host:

- **CPU lane:** builds, test shards, compilation, extraction, indexing, and data transforms.
- **RAM lane:** large dependency graphs, datasets, multiple isolated worktrees, and CPU offload.
- **GPU lane:** CUDA, local inference, embeddings, reranking, vision encoders, and bounded ML experiments.

The logical name `compute` better describes the role. `gpu` can remain a compatibility alias if scripts already expect it.

Suggested starting policy, to validate after live access is restored:

- one GPU-exclusive job at a time;
- no more than four CPU-heavy workers initially;
- light coding may run concurrently only while memory, thermals, and GPU-serving latency remain healthy;
- every agent uses its own Git worktree; no shared live source directory.

These are safe initial limits, not measured capacity claims.

### DEPLOY — services, data, and storage

`vphk2001-GE62-6QC` should converge toward a boring service node. It already hosts databases, containers, tunnels, and Research Wiki services. The audit shows interactive Python/OpenCode/VS Code work saturating its four CPU cores, so new builds, tests, indexing, or agents should not be scheduled there while that pressure remains.

Its GTX 960M 2 GB is live and idle, but it is not a useful substitute for the RTX 4060 Ti. Keep it optional for tiny experiments or display duties; do not route primary model serving to it.

## Current fabric

![Current three-machine fabric](diagrams/current-fabric.png)

Source: [current-fabric.mmd](diagrams/current-fabric.mmd) · [SVG](diagrams/current-fabric.svg)

Solid arrows are currently verified. Dashed arrows are intended or only partially verified.

## Workload routing

![Workload routing](diagrams/workload-routing.png)

Source: [workload-routing.mmd](diagrams/workload-routing.mmd) · [SVG](diagrams/workload-routing.svg)

## Placement matrix

| Workload | Primary | Fallback | Gate |
| --- | --- | --- | --- |
| Architecture, planning, browser research | DEV | Cloud frontier model | Keep local interaction responsive |
| Editing and short unit tests | DEV | COMPUTE CPU/RAM lane | COMPUTE needs verified SSH and isolated worktree |
| Light coding agent | COMPUTE CPU/RAM lane | DEV | Admit only after load, RAM, and worktree ownership check |
| Large build or test shard | COMPUTE CPU lane | Queue | Do not spill onto DEPLOY under current load |
| Extraction, indexing, batch transforms | COMPUTE CPU/RAM lane | Queue | Bound concurrency and disk use |
| CUDA, embeddings, reranking, local inference | COMPUTE GPU lane | Cloud API | One GPU-exclusive job initially |
| Persistent databases and APIs | DEPLOY | None until failover exists | Protect service latency and storage |
| Staging deployment | DEPLOY | None until failover exists | Git commit/image plus health check |
| Large artifacts and datasets | DEPLOY storage | Future object store | Prefer wired path; avoid source-code sharing |

## Admission gate for every remote job

Before dispatching work, check:

1. identity and reachability;
2. current CPU load, free/available RAM, swap, and disk headroom;
3. active writers and process ownership;
4. target worktree, branch, and clean/dirty state;
5. job concurrency and whether it competes with a serving workload;
6. an explicit result path: Git commit, test result, or immutable artifact.

If a gate cannot be checked, queue the task instead of guessing.

## Coordination contracts

- **Source:** Git branches and worktrees.
- **Heavy execution:** read-only dispatch first; writes only inside an issue-owned worktree after authorization.
- **Artifacts:** explicit paths or a future object store; never a shared live checkout.
- **Deployment:** immutable commit or image, then health check.
- **Secrets:** environment or secret store only; never repository configuration.
