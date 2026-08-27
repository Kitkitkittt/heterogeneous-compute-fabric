# COMPUTE inventory

Status: partial audit on 2026-08-27. Network identity was live; SSH/22 timed out.

## Live-verified

| Area | Observation |
| --- | --- |
| Host | `desktop-x2w7f` |
| OS family | Windows, from Tailscale peer metadata |
| Tailscale | Reachable through relay; direct path not established |
| SSH | Blocked before authentication; no live inventory captured |

## Inherited from the committed handoff—not re-verified

| Area | Prior observation |
| --- | --- |
| CPU | Intel Core i5-12400F, 6 cores / 12 threads |
| Memory | 48 GB |
| GPU | RTX 4060 Ti 16 GB |
| Storage | Samsung SSD 980 500 GB plus Seagate 2 TB disk |
| OS | Windows 11 Enterprise build 26200 |

## Recommended role

Treat the machine as a hybrid worker:

- **Light coding:** isolated agent worktrees, secondary editor sessions, bounded unit tests.
- **CPU compute:** compilation, test shards, extraction, indexing, data preparation.
- **RAM compute:** larger datasets, concurrent dependency graphs, CPU offload.
- **GPU compute:** CUDA, local inference, embeddings, reranking, vision, bounded training experiments.

## Initial scheduling hypothesis

- One GPU-exclusive job at a time.
- Start with at most four CPU-heavy workers.
- Reserve enough CPU/RAM for the Windows desktop and GPU-serving process.
- Admit light coding only after live load, memory, thermals, disk, and worktree ownership are verified.

These limits are intentionally conservative and must be benchmarked after access is restored.

