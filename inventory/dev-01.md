# `dev-01` public inventory

Admission state: `install_pending`

Target OS Profile: `ubuntu24`; `pop24` is an allowed workstation exception.

## Hardware Assignment

| Component | Public specification | Evidence |
| --- | --- | --- |
| System | Lenovo 83AA | Verified, chassis, 2026-08-27 |
| CPU | AMD Ryzen 7 7840S, 8 cores / 16 threads, x86_64 | Verified, chassis, 2026-08-27 |
| Memory | 32 GiB, four 8 GiB LPDDR5-6400 devices | Verified, chassis, 2026-08-27 |
| GPU | AMD Radeon 780M integrated graphics, shared memory | Verified, chassis, 2026-08-27 |
| Internal storage | Samsung 1 TB NVMe | Verified, chassis, 2026-08-27 |
| External storage | 500 GB USB disk; exact model unknown | Verified capacity, chassis, 2026-08-27 |
| Network capability | Wi-Fi 6E and USB Ethernet observed | Verified capability; live route omitted |

## Intended roles

- interactive development and browser work;
- control and Git coordination;
- short local tests and light CPU work;
- small graphics or inference experiments when a fresh resource snapshot permits.

## Unknowns and gates

- Reconfirm hardware after the reinstall and record any changed assignment.
- Pass live-media display, suspend/resume, audio, Ethernet, Wi-Fi, Bluetooth, USB, and browser-acceleration checks before erasing the current installation.
- Record backup and sample-restore evidence privately.
- Verify private networking, key-only SSH, Git, isolated worktrees, and a container smoke test after installation.
- Do not convert old Windows free-memory, disk-space, tool, or network observations into Linux admission evidence.

