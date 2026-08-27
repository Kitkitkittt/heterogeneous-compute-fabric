# DEV inventory

Status: live local audit completed 2026-08-27 12:47 UTC+07:00.

| Area | Verified observation |
| --- | --- |
| Host | `KeithVo`; Lenovo 83AA |
| OS | Windows 11 Home, build 26200, 64-bit |
| CPU | Ryzen 7 7840S, 8 cores / 16 threads |
| Memory | 32 GiB installed LPDDR5-6400; about 27.8 GiB visible; about 4.5 GiB free at snapshot |
| GPU | Radeon 780M integrated graphics; shared system memory |
| Primary disk | Samsung 1 TB NVMe, healthy |
| External disk | 500 GB USB disk, healthy |
| Active physical network | 100 Mbps USB Ethernet |
| Private network | Tailscale client running |
| SSH | Client available; inbound `sshd` not observed |
| Coding tools | Git, Python, Node, uv available; Rust/Cargo absent from `PATH` |
| Containers | Docker client present; daemon unavailable |

## Recommended role

- Primary human interaction and control plane.
- Planning, code editing, browser work, Git coordination, and short tests.
- Small local inference experiments only when memory headroom is sufficient.
- Avoid persistent databases, large builds, and bulk artifact transfer over the current 100 Mbps link.

## Gate before work

Check free memory and link choice. At the audit snapshot, memory—not CPU—was the immediate local constraint.

