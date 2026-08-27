# Three-machine read-only audit — 2026-08-27

## Audit contract

- Window: 2026-08-27 12:47–12:49, UTC+07:00.
- Origin: `KeithVo`.
- Remote boundary: identity, inventory, resource, network, process, service, listener, and tool-version reads only.
- No packages, services, firewall rules, SSH settings, files, containers, databases, or machine configuration were changed.
- Repository documentation is the only state changed by this work.
- Public-repository sanitization: no private/Tailscale IP addresses, MAC addresses, machine IDs, keys, tokens, or credentials are recorded here.

## Executive result

| Node | Capability | Audit status | Operating status |
| --- | --- | --- | --- |
| DEV / `KeithVo` | 8C/16T Zen 4, 32 GB installed, Radeon 780M, 1 TB NVMe | Live local audit complete | **Yellow:** CPU healthy; low free RAM, 100 Mbps active Ethernet, no inbound SSH service observed |
| COMPUTE / `desktop-x2w7f` | Prior record: 6C/12T, 48 GB, RTX 4060 Ti 16 GB | **Partial:** Tailscale live; SSH/22 timed out | **Red gate:** do not claim remote dispatch readiness until identity and live inventory pass |
| DEPLOY / `vphk2001-GE62-6QC` | 4C/4T, 23 GiB usable, NVMe + USB SSD/HDD, GTX 960M 2 GB | Live SSH audit complete | **Red for added compute:** load far exceeds core count; persistent services remain online |

## Connectivity evidence

| From `KeithVo` | Tailscale | SSH | Result |
| --- | --- | --- | --- |
| `desktop-x2w7f` | Reply via Singapore relay, about 93 ms | TCP/22 timed out | Network identity is visible; SSH-based audit blocked |
| `vphk2001-GE62-6QC` | Reply via Singapore relay, about 160 ms | Batch-mode identity check passed | Read-only Linux audit completed |
| `KeithVo` inbound | Local Tailscale client running | No `sshd` service observed | The planned `ssh dev` identity is not proven |

Neither remote peer established a direct Tailscale path during the probe. No throughput benchmark was attempted because the audit forbids starting a remote test listener.

## DEV findings

- Lenovo model 83AA; Windows 11 Home build 26200.
- Ryzen 7 7840S: 8 cores, 16 logical processors; sampled load 9%.
- Four 8 GiB LPDDR5-6400 modules are installed. Windows reported about 27.8 GiB visible and about 4.5 GiB free at the snapshot; integrated-GPU reservation and current workload explain why installed and visible memory differ.
- Radeon 780M reported healthy. Windows reports roughly 4 GiB adapter memory; this is not evidence of 4 GiB dedicated VRAM.
- Samsung 1 TB NVMe reported healthy. The Windows volumes on it had roughly 52 GiB free on `C:` and 76 GiB free on `D:`.
- External 500 GB USB disk reported healthy, with roughly 393 GiB free.
- The active physical adapter was a 100 Mbps USB Ethernet device. Wi-Fi 6E existed but was disconnected.
- Git 2.49, Python 3.12, Node 24, uv 0.6, OpenSSH client, and Tailscale were available.
- Rust/Cargo were not on `PATH`. Docker client existed, but its daemon was not running.

Conclusion: DEV is a good control/editing node, but memory pressure and the 100 Mbps link should be checked before launching multiple local agents or moving large artifacts.

## COMPUTE findings

Live facts:

- Tailscale reported `desktop-x2w7f` online as Windows.
- A Tailscale ping returned through the Singapore relay.
- SSH on port 22 timed out before authentication; therefore hostname, user, live load, free memory, disks, driver, CUDA, and toolchain were not observed.

Inherited facts from the committed handoff, not re-verified in this audit:

- Intel Core i5-12400F, 6 cores / 12 threads.
- 48 GB system RAM.
- RTX 4060 Ti 16 GB.
- Samsung SSD 980 500 GB and a 2 TB Seagate disk.
- Windows 11 Enterprise build 26200.

Conclusion: the hardware description supports the proposed hybrid CPU/RAM/GPU role and light coding. Operational readiness remains blocked until read-only SSH identity and live capacity checks pass.

## DEPLOY findings

- MSI GE62 6QC; Ubuntu 24.04.4 LTS; kernel 7.0.0-30-generic.
- Intel Core i5-6300HQ: 4 cores / 4 threads.
- Load average was 8.49 / 9.56 / 11.99—roughly 2.1x to 3.0x the available CPU count.
- Memory: 23 GiB total, 17 GiB available; swap: 47 GiB total, 9.9 GiB used.
- Top sampled consumers included Python near one full core and multiple long-running OpenCode and VS Code processes consuming several additional cores in aggregate.
- Root storage: Samsung 512 GB NVMe, 62% used, about 169 GiB available.
- External Crucial 1 TB SSD over USB/NTFS, about 871 GiB available.
- External Toshiba 4 TB-class HDD over USB. Two mounted ext4 partitions provide about 1.8 TiB and 646 GiB filesystems. The visible partition sizes do not account for roughly 1.2 TB of the physical device; this requires a separate, authorized partition-table review before any capacity claim.
- Active uplink was Intel AC 3165 Wi-Fi. The Killer E2400 gigabit Ethernet controller existed but was down.
- Intel HD 530 and NVIDIA GTX 960M were present. NVIDIA reported driver 580.173.02, CUDA 13.0 compatibility, 2 GiB VRAM, 0% utilization.
- Running services included Docker/containerd, three PostgreSQL clusters, Cloudflare tunnels, Tailscale, 9Router, Research Wiki 0.5.4, Glances, TeamViewer, and desktop services. Redis and MongoDB processes were also observed.
- PostgreSQL listeners were loopback-only in the snapshot. A Next.js listener was exposed on all interfaces. Docker service was running, but the audit user lacked permission to query the Docker API.

Conclusion: DEPLOY has useful storage and its serving stack is alive, but interactive development is consuming the CPU budget. Do not add heavy jobs; first move or stop those workloads under their owners' authority.

## Corrections to the initial handoff

1. `desktop-x2w7f` should be described as a hybrid compute node, not a GPU-only node.
2. DEPLOY has a live GTX 960M 2 GB, but it remains irrelevant to primary AI routing.
3. DEPLOY storage is now tied to physical devices and buses: NVMe root, USB SSD, and USB HDD.
4. The apparent 3.6 TB HDD capacity is not fully represented by mounted partitions; do not equate mount totals with a complete storage plan.
5. Current connectivity is relay-based, not direct, and stable `dev`/`compute`/`deploy` SSH aliases are not yet proven.
6. DEPLOY is actively oversubscribed and cannot safely absorb more coding or batch work.

## Next gates—not performed

1. On COMPUTE, restore/authorize SSH access and repeat the Windows inventory commands.
2. On DEV, decide whether inbound SSH is actually needed; if so, authorize a separate configuration change.
3. Recheck all three nodes on wired networking and measure throughput with an explicitly authorized temporary listener.
4. Identify owners of the high-CPU processes on DEPLOY before moving or stopping anything.
5. After the above, run one bounded Git-based workflow: edit on DEV, test/build on COMPUTE, deploy and health-check on DEPLOY.

