# `deploy-01` public inventory

Admission state: `verified`, with scheduling gates still open

The existing Ubuntu installation is not part of the DEV/COMPUTE reinstall sequence.

## Hardware Assignment

| Component | Public specification | Evidence |
| --- | --- | --- |
| System | MSI GE62 6QC | Verified, chassis, 2026-08-27 |
| CPU | Intel Core i5-6300HQ, 4 cores / 4 threads, x86_64 | Verified, chassis, 2026-08-27 |
| Memory | 23 GiB visible; module layout/speed unknown | Verified, installation, 2026-08-27 |
| Graphics | Intel HD 530 | Verified, chassis, 2026-08-27 |
| Discrete GPU | NVIDIA GTX 960M, 2 GB VRAM | Verified, chassis, 2026-08-27 |
| Internal storage | Samsung 512 GB NVMe | Verified, chassis, 2026-08-27 |
| External storage | Crucial 1 TB USB SSD | Verified, chassis, 2026-08-27 |
| External storage | Toshiba 4 TB-class USB HDD | Verified, chassis, 2026-08-27 |
| Network capability | Wi-Fi and Killer E2400 gigabit Ethernet | Verified capability; live route omitted |

## Intended roles

- persistent services and databases;
- staging and deployment;
- owned storage and immutable artifacts.

The legacy GPU is not a primary AI scheduling target.

## Gates

- Map service and data owners, recovery locations, and credential references privately.
- Record a resource budget before adding work; serving continuity has priority.
- Verify backups with a sample restore and define deployment rollback.
- Resolve the complete storage/partition map privately before making capacity claims.
- Do not expose listener, process, or service details in the public inventory.

