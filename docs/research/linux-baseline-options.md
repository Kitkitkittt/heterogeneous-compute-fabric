# Linux baseline options for the compute fabric

Status: decision evidence

Evidence date: 2026-08-27

Scope: `dev-01` (AMD Ryzen 7 7840S / Radeon 780M workstation) and `compute-01` (Intel Core i5-12400F / NVIDIA RTX 4060 Ti CUDA worker)

## Decision

Use **Ubuntu 24.04 LTS as the v1 operational baseline**, especially for `compute-01`.

- Install Ubuntu 24.04 LTS on `compute-01` and keep it headless-first. This is the lowest-friction option for the official Docker, NVIDIA driver/CUDA, and NVIDIA Container Toolkit paths.
- Ubuntu 24.04 LTS is also the simplest choice for `dev-01` if one bootstrap, one package family, and one troubleshooting playbook matter most.
- Pop!_OS 24.04 LTS is an acceptable **workstation exception for `dev-01`** if COSMIC and its desktop experience are preferred. Treat it as a separate `pop24` profile, not as identical to Ubuntu.
- Fedora Workstation 44 is interoperable and technically viable, particularly as a developer desktop, but should not be the v1 baseline. Its shorter lifecycle and different package/upgrade path increase upkeep, and NVIDIA does not list Fedora in the Container Toolkit qualification table.

This is not a claim that Pop!_OS or Fedora cannot work. It separates **interoperability** from **same operational baseline**.

## Evidence matrix

| Criterion | Ubuntu 24.04 LTS | Pop!_OS 24.04 LTS | Fedora Workstation 44 |
| --- | --- | --- | --- |
| Current status | Supported LTS; standard security maintenance through May 2029 | Current Pop!_OS release and designated LTS | Current Workstation release as of the evidence date; released 2026-04-28 |
| Package/upgrade family | `apt`; Canonical LTS lifecycle | Ubuntu-derived `apt`, plus System76 repositories and `pop-upgrade` | `dnf`; Fedora release upgrades |
| Tailscale | Official Linux installer supports Ubuntu-based distributions | Covered as Ubuntu-based | Official Linux installer supports Fedora and derivatives |
| Docker Engine | Docker explicitly supports Ubuntu 24.04 on amd64 and arm64 | Likely workable, but Docker says derivative distributions are not tested or officially supported | Docker explicitly supports maintained Fedora 44 and 43 |
| NVIDIA driver and CUDA | NVIDIA lists Ubuntu 24.04 amd64 as supported and validated | System76 offers an NVIDIA image and Pop!_OS 24.04 initially ships NVIDIA driver 580; Pop!_OS is not named in NVIDIA's native CUDA OS table | NVIDIA lists Fedora 44 x86_64 as supported; its validated CUDA configuration table may lag the current Fedora release |
| NVIDIA Container Toolkit | NVIDIA lists Ubuntu 24.04 amd64 as tested and expected to work | Install instructions cover Debian-derived systems, but Pop!_OS is absent from the qualification table | `dnf` installation instructions exist, but Fedora is absent from the qualification table |
| Security/firmware caveat | No exception identified in the sources reviewed | System76 requires Secure Boot to be disabled for installation | No exception identified in the sources reviewed |
| Best fit here | Canonical baseline for both roles; strongest fit for CUDA worker | Optional DEV desktop profile | Optional future workstation/lab profile with explicit upgrade ownership |

## What “interoperates” means

A mixed Ubuntu/Pop!_OS/Fedora fabric can still use the same network and workload contracts:

- Tailscale connectivity and SSH;
- Git remotes, issue-owned branches, and isolated worktrees;
- OCI/Docker images built for the correct CPU architecture;
- a machine-readable node registry and role/capability labels;
- explicit artifact, test-result, and deployment handoffs.

Therefore, choosing Pop!_OS or Fedora for `dev-01` does **not** inherently break communication with Ubuntu nodes.

## What a “same operational baseline” adds

The same distribution reduces conditional logic in:

- package names, repositories, and bootstrap commands;
- Docker and NVIDIA installation paths;
- OS upgrade cadence and recovery procedures;
- service, firewall, and security-policy troubleshooting;
- acceptance tests and the evidence an agent must collect after rebuilds.

Pop!_OS remains Ubuntu-derived, but Docker explicitly warns that derivative distributions are not tested or verified, and NVIDIA's tested Container Toolkit matrix names Ubuntu rather than Pop!_OS. Fedora has first-party Docker and NVIDIA driver/CUDA paths, but uses a different package family and a faster release lifecycle. Those are maintenance differences, not network incompatibilities.

## Role-specific assessment

### `dev-01`: Ryzen/Radeon workstation

No CUDA or NVIDIA Container Toolkit requirement controls this node. Pop!_OS 24.04 is a credible option because its documented initial stack includes Linux 6.17.9 and Mesa 25.1.5-1. Fedora 44 and Ubuntu 24.04 are also viable candidates.

Because the reviewed first-party sources do not provide a complete device-level matrix for this exact Ryzen/Radeon system, the final choice must pass a live-media acceptance gate before installation:

1. internal and external displays;
2. suspend/resume and shutdown/reboot;
3. Ethernet, Wi-Fi, Bluetooth, audio, and USB;
4. browser hardware acceleration and a short graphics stress test;
5. Tailscale, SSH, Git, editor, and container smoke tests.

**Recommendation:** choose Ubuntu 24.04 for maximum operational uniformity, or Pop!_OS 24.04 if the workstation experience is worth maintaining one small profile exception. Do not choose Pop!_OS without explicitly accepting its Secure Boot requirement.

### `compute-01`: Intel/NVIDIA CUDA worker

The decisive requirement is a reproducible CUDA container path. Ubuntu 24.04 is explicitly supported by Docker, listed in NVIDIA's driver/CUDA matrix, and listed in NVIDIA Container Toolkit's tested-platform table. Fedora 44 has official Docker and NVIDIA driver/CUDA paths, but is not in the current Container Toolkit qualification table. Pop!_OS offers convenient NVIDIA desktop media, but is a derivative rather than a named Docker or CUDA qualification target.

**Recommendation:** Ubuntu 24.04 LTS, headless-first, with the distribution package-manager driver path and a pinned, tested NVIDIA Container Toolkit version. Validate with `nvidia-smi`, a host CUDA smoke test, and a GPU-enabled container before admitting workloads.

## Guardrails for a mixed DEV exception

If `dev-01` uses Pop!_OS while `compute-01` uses Ubuntu:

1. keep a common contract layer for SSH, Tailscale, Git, container invocation, and artifact paths;
2. maintain separate `ubuntu24` and `pop24` bootstrap profiles;
3. keep CUDA execution on `compute-01`; do not make DEV desktop packaging part of the CUDA worker contract;
4. publish multi-architecture images only when both amd64 and arm64 variants pass tests;
5. record OS family and version as replaceable node-assignment facts, not in the stable node ID;
6. require the same post-install acceptance report from every profile.

## Official sources

- Canonical: [Ubuntu release cycle](https://ubuntu.com/about/release-cycle) and [Ubuntu release list](https://ubuntu.com/project/docs/release-team/list-of-releases/)
- System76: [Pop!_OS 24.04 installation](https://support.system76.com/support/install-pop/), [Pop!_OS 24.04 components](https://support.system76.com/support/default-apps), and [Pop!_OS upgrade path](https://support.system76.com/support/upgrade-pop)
- Fedora Project: [Fedora Workstation download/current release](https://www.fedoraproject.org/workstation/download/) and [Fedora release lifecycle](https://docs.fedoraproject.org/en-US/releases/lifecycle/)
- Tailscale: [Install Tailscale on Linux](https://tailscale.com/docs/install/linux)
- Docker: [Install Docker Engine](https://docs.docker.com/engine/install/), [Ubuntu requirements](https://docs.docker.com/engine/install/ubuntu/), and [Fedora requirements](https://docs.docker.com/engine/install/fedora/)
- NVIDIA: [Driver and CUDA Linux system requirements](https://docs.nvidia.com/datacenter/tesla/driver-installation-guide/introduction.html), [Container Toolkit platform support](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/supported-platforms.html), and [Container Toolkit installation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

## Revalidation rule

Re-check this note before a reinstall if it is more than 30 days old. OS releases, vendor support matrices, driver branches, Docker repositories, and NVIDIA Container Toolkit versions are time-sensitive.
