# `compute-01` public inventory

Admission state: `install_pending`

Target OS Profile: `ubuntu24`, headless-first.

## Hardware Assignment

| Component | Public specification | Evidence |
| --- | --- | --- |
| System | Exact chassis/mainboard unknown | Unknown |
| CPU | Intel Core i5-12400F, 6 cores / 12 threads, x86_64 | Inherited from prior handoff |
| Memory | 48 GB; module layout and speed unknown | Inherited from prior handoff |
| GPU | NVIDIA RTX 4060 Ti, 16 GB VRAM | Inherited from prior handoff |
| Internal storage | Samsung SSD 980, 500 GB | Inherited from prior handoff |
| Data storage | Seagate 2 TB disk; media type unknown | Inherited from prior handoff |
| Network capability | Controller and link capability unknown | Unknown |

## Intended roles

- x86_64 CPU builds and tests;
- memory-heavy coding, builds, and data preparation;
- NVIDIA CUDA tests and GPU-enabled containers;
- local inference and bounded batch work.

The node is useful without its GPU. CPU, RAM, and CUDA are separate scheduling lanes.

## Current evidence boundary

Private networking, TCP/22, and the SSH daemon were verified on the disposable Windows installation. Operator key authorization and live hardware inventory were not completed. The planned Linux reinstall invalidates the installation evidence in either case.

## Unknowns and gates

- Verify chassis, mainboard, RAM layout/speed, GPU identity, storage media, disk health, and network capability.
- Record backup, volume ownership, partition plan, and sample-restore evidence privately before reinstall.
- Verify Ubuntu boot, private networking, key-only SSH, updates, time synchronization, and firewall policy.
- Verify the supported NVIDIA driver path, `nvidia-smi`, a bounded host GPU test, NVIDIA Container Toolkit, and a GPU-enabled container.
- Record bounded CPU/GPU thermals and storage headroom.
- Verify Git, an issue-owned branch, and an isolated worktree before admission.

