# DEPLOY inventory

Status: live SSH audit completed 2026-08-27 12:48–12:49 UTC+07:00.

| Area | Verified observation |
| --- | --- |
| Host | `vphk2001-GE62-6QC`; MSI GE62 6QC |
| OS | Ubuntu 24.04.4 LTS; kernel 7.0.0-30-generic |
| CPU | Intel Core i5-6300HQ, 4 cores / 4 threads |
| Load | 8.49 / 9.56 / 11.99 at snapshot—well above CPU count |
| Memory | 23 GiB total; 17 GiB available |
| Swap | 47 GiB total; 9.9 GiB used |
| Primary disk | Samsung 512 GB NVMe; root 62% used, about 169 GiB available |
| External SSD | Crucial 1 TB USB SSD; about 871 GiB available |
| External HDD | Toshiba 4 TB-class USB HDD; two mounted ext4 partitions; partition map does not account for all physical capacity |
| Active network | Intel AC 3165 Wi-Fi; gigabit Ethernet controller present but down |
| GPUs | Intel HD 530 plus GTX 960M 2 GB; NVIDIA driver 580.173.02; CUDA 13.0 compatibility |
| Services | Docker/containerd, PostgreSQL, Cloudflare tunnels, Tailscale, 9Router, Research Wiki, Glances, TeamViewer, Redis/MongoDB processes |
| Docker access | Service running; audit user cannot query Docker API |

## Recommended role

- Persistent databases, APIs, staging, tunnels, scheduled low-impact jobs, and storage.
- No new heavy builds, tests, indexing, inference, or interactive coding under the current load.
- Move interactive agent/editor work to DEV or COMPUTE only under the owning session's authority.
- Prefer the wired gigabit interface before using this node for large artifact movement.

## Immediate gate

The machine is serving but CPU-oversubscribed. Identify process owners and protect service latency before assigning more work. No process was stopped or changed during this audit.

