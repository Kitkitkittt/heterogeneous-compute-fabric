# Four-node sanitized audit — 2026-08-27

Status: historical evidence; installation and snapshot facts require revalidation

This public record preserves the capacity findings needed for planning while excluding operational identities and live infrastructure details.

## Audit boundary

- Local and remote inventory was read-only.
- No package, service, firewall, storage, workload, or cloud configuration was changed by the audit.
- A later human action installed the Windows OpenSSH Server on the current `compute-01` installation; this proved transport but did not authorize key access.
- Hostnames, addresses, SSH users, regions, service names, listeners, process details, credentials, and exact live utilization are deliberately omitted.

## Evidence summary

| Node Slot | Durable capacity | Evidence status | Admission result |
| --- | --- | --- | --- |
| `dev-01` | Ryzen 7 7840S, 8C/16T; 32 GiB LPDDR5-6400; Radeon 780M; 1 TB NVMe; 500 GB USB disk | Hardware verified locally | `install_pending`; installation evidence will be invalidated |
| `compute-01` | Core i5-12400F, 6C/12T; 48 GB; RTX 4060 Ti 16 GB; 500 GB SSD; 2 TB disk | Hardware inherited; network transport and SSH daemon verified | `install_pending`; live hardware verification required |
| `cloud-01` | OCI A1 Flex ARM64; 4 OCPUs; 24 GB; 50 GB-class boot volume | Allocation verified from the instance | `verified`, but cost/ownership/storage gates remain |
| `deploy-01` | Core i5-6300HQ, 4C/4T; 23 GiB visible; Intel HD 530; GTX 960M 2 GB; 512 GB NVMe; 1 TB USB SSD; 4 TB-class USB HDD | Hardware verified remotely | `verified`, but owner/capacity/recovery gates remain |

## Connectivity conclusion

Private networking reaches every audited remote Node Slot. On the current `compute-01` installation, TCP/22 and the SSH daemon are now verified; authentication remains intentionally fail-closed until an operator public key is authorized. A fresh Linux installation will replace these installation facts, so they are not admission evidence for the target state.

## Durable findings

### `dev-01`

- Lenovo 83AA hardware assignment.
- Ryzen 7 7840S with 8 cores and 16 threads.
- 32 GiB LPDDR5-6400 presented as four 8 GiB devices.
- Radeon 780M integrated graphics with shared system memory.
- Samsung 1 TB NVMe and a 500 GB USB disk.
- Wi-Fi 6E capability and a USB Ethernet path were observed; throughput belongs in private snapshot evidence.

### `compute-01`

The following hardware came from prior handoff evidence and remains `inherited` until a live verification issue passes:

- Intel Core i5-12400F with 6 cores and 12 threads.
- 48 GB system memory; module layout and speed unknown.
- NVIDIA RTX 4060 Ti with 16 GB VRAM.
- Samsung SSD 980 500 GB and a 2 TB Seagate disk.

The observed SSH service proves only the current Windows installation's transport. It does not verify GPU driver, CUDA, disk health, thermals, active writers, or Linux suitability.

### `cloud-01`

- OCI A1 Flex ARM64 allocation using Neoverse-N1 CPUs.
- Four OCPUs and 24 GB configured memory.
- 50 GB-class boot volume; exact performance, backup policy, and billing status remain outside the public record.

### `deploy-01`

- MSI GE62 6QC hardware assignment.
- Intel Core i5-6300HQ with 4 cores and 4 threads.
- 23 GiB memory visible to the current installation.
- Intel HD 530 and NVIDIA GTX 960M with 2 GB VRAM.
- Samsung 512 GB NVMe, Crucial 1 TB USB SSD, and Toshiba 4 TB-class USB HDD.
- Intel AC 3165 Wi-Fi and Killer E2400 gigabit Ethernet capability.

## Evidence lifetime correction

Earlier drafts mixed chassis facts with temporary OS, service, disk-usage, and process snapshots. This record supersedes them:

- hardware above is `chassis` evidence;
- OS, drivers, packages, keys, and network registration are `installation` evidence;
- load, free memory, free disk, listeners, services, and temperature are `snapshot` evidence.

Reinstalling `dev-01` or `compute-01` invalidates all prior installation and snapshot evidence. Hardware must still be checked for changes before admission.

## Unperformed gates

1. Human backup, recovery, and reinstall evidence for `compute-01`.
2. Agent verification of `compute-01` hardware, disks, private networking, SSH, NVIDIA driver, CUDA container, thermals, Git, and worktree isolation.
3. Equivalent human reinstall and agent workstation verification for `dev-01`.
4. Private cost, ownership, storage, and recovery review for `cloud-01`.
5. Private service ownership, resource budget, storage map, and recovery review for `deploy-01`.
6. A bounded Git-to-worker-to-deployment pilot.

