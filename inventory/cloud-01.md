# `cloud-01` public inventory

Admission state: `verified`, with scheduling gates still open

The existing Linux installation is not part of the DEV/COMPUTE reinstall sequence.

## Allocated capacity

| Component | Public specification | Evidence |
| --- | --- | --- |
| Shape | OCI `VM.Standard.A1.Flex` | Verified allocation, 2026-08-27 |
| CPU | Arm Neoverse-N1, 4 OCPUs, arm64 | Verified allocation, 2026-08-27 |
| Memory | 24 GB configured | Verified allocation, 2026-08-27 |
| Storage | 50 GB-class OCI boot volume | Verified allocation, 2026-08-27 |

This describes virtual allocation, not physical host hardware or billing status.

## Intended roles

- bounded ARM64 builds and tests;
- lightweight agents with explicit resource limits;
- architecture-compatible auxiliary services.

## Gates

- Confirm cost and eligibility in the authenticated cloud account.
- Map current workload owners, data, backups, and recovery paths privately.
- Confirm current storage headroom before scheduling new work.
- Require every repository or container to declare ARM64 support.
- Keep tenancy, region, instance, network, and volume identifiers out of this repository.

