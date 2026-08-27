# Reinstall and admit a node

This is a documentation contract for a human operator and a separate verification agent. It does not authorize this documentation task to reinstall a machine.

## Issue workflow

Create two dependency-linked issues per node:

1. **Human reinstall issue** — label `ready-for-human` and `node:<node-id>`.
2. **Agent verification issue** — blocked by the reinstall issue; label `ready-for-agent` only after the human records completion evidence.

The verification issue closes only when its acceptance report supports `schedulable`. Otherwise use `needs-info` or `ready-for-human` and keep the node fail-closed.

## Before the human reinstall

- Resolve the exact Node Slot and Hardware Assignment from the public and private registries.
- Record current disk/partition ownership, services, local-only files, repositories, credential references, and encryption/recovery requirements privately.
- Produce a backup and verify at least one representative restore.
- Confirm which disks may be erased and which must remain untouched.
- Confirm firmware mode, Secure Boot policy, installation media checksum, network path, and recovery media.
- For `dev-01`, pass the live-media workstation matrix before erasing the current OS.
- For `compute-01`, confirm the GPU and storage devices are visible and the intended Ubuntu/NVIDIA path is supported.

If any ownership, restore, or target-disk fact is unknown, stop and apply `needs-info`.

## Human installation record

The human issue should record, without public operational identifiers:

- Node Slot and selected OS Profile;
- installation-media version and checksum;
- explicit target disk and preserved disks;
- encryption and recovery-key storage confirmation;
- installation completion and reboot result;
- creation of the operator account and readiness for private-network/key bootstrap;
- unexpected hardware, partition, firmware, or driver findings.

Never paste secrets, hostnames, private addresses, usernames, or recovery keys into a public issue.

## Base agent verification

The verification agent collects a sanitized acceptance report and private operational evidence:

1. identity maps to the intended Node Slot in the private overlay;
2. OS Profile and architecture match policy;
3. CPU, memory, GPU, storage, and network hardware match or update the assignment;
4. disk layout, health, encryption, and headroom pass;
5. time synchronization, updates, firewall, private networking, and key-only SSH pass;
6. Git can create an issue-owned branch in an isolated worktree;
7. container runtime smoke test passes;
8. bounded CPU, memory, storage, network, and thermal observations are acceptable;
9. no unexpected active writers, services, or ownership conflicts exist.

Promote each evidence field independently. Do not mark the whole node `verified` when some hardware remains inherited or unknown.

## `compute-01` role gates

In addition to base verification:

- install the NVIDIA driver through the documented Ubuntu package path;
- verify `nvidia-smi` and the expected GPU/VRAM;
- run a bounded host GPU smoke test;
- install and pin a supported NVIDIA Container Toolkit version;
- run a GPU-enabled container smoke test;
- record driver, CUDA compatibility, toolkit, and test-image versions;
- verify CPU/RAM work independently of CUDA.

Do not admit the `cuda` role merely because the GPU appears in PCI inventory.

## `dev-01` workstation gates

In addition to base verification:

- internal/external displays and browser acceleration;
- suspend/resume, shutdown, and reboot;
- Ethernet, Wi-Fi, Bluetooth, audio, and USB;
- editor/toolchain and a short graphics test;
- Tailscale, SSH, Git, and container smoke tests.

If `pop24` is selected, record it as an explicit profile exception and apply the profile's Secure Boot and upgrade guidance. Do not silently reuse an `ubuntu24` acceptance report.

## Admission update

The verification commit must update:

- `inventory/nodes.yaml` admission state and field evidence;
- the matching `inventory/<node-id>.md` record;
- the issue acceptance report with sanitized pass/fail results;
- the private overlay with connection, owner, recovery, and snapshot details.

Only then transition `installed -> verified -> schedulable`. A node can remain `verified` with one or more roles gated.

## Machine-readable report handoff

Use the versioned admission-observation contract to separate collection from evaluation. Start from the matching COMPUTE or DEV example, fill only directly observed checks, and leave every unobserved check as `unknown`.

Generate the public-safe report with:

```powershell
uv run fabric admission report `
  --profile NODE_SLOT `
  --observations PATH_TO_OBSERVATIONS `
  --view public `
  --format json
```

Store a `private` view only in the authorized Private Operations Overlay workflow. Never paste it into a public issue. The evaluator can admit passed Roles independently; update the Public Registry only from its public output plus reviewed evidence.

