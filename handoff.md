# Three-Machine Agentic Coding / Local AI Cluster

## 0. Objective

I currently own three heterogeneous machines. The goal is **not** to merge them into one virtual supercomputer.

The goal is to build a small personal compute fabric for:

1. Agentic coding across multiple machines
2. Local small/medium LLM inference
3. CUDA / ML experimentation
4. Parallel builds, tests, indexing, extraction and data jobs
5. Persistent databases and services
6. Deployment / staging
7. Remote operation through SSH
8. Eventually simple resource-aware agent orchestration

Target architecture:

```text
                        CLOUD FRONTIER MODELS
                     Claude / OpenAI / others
                               │
                               │ API
                               ▼
                    ┌──────────────────────┐
                    │  DEV / CONTROL NODE  │
                    │ Ryzen 7 7840S / 32G  │
                    │ Linux                │
                    └──────────┬───────────┘
                               │
                   SSH / HTTP / Git / APIs
               ┌───────────────┴────────────────┐
               │                                │
               ▼                                ▼
     ┌────────────────────┐          ┌────────────────────┐
     │ GPU COMPUTE NODE   │          │ DEPLOY / DATA NODE │
     │ i5-12400F / 48GB   │          │ i5-6300HQ / 24GB   │
     │ RTX 4060 Ti 16GB   │          │ Ubuntu 24.04       │
     └────────────────────┘          └────────────────────┘
               │                                │
         CUDA / LLMs                    Docker / DB / storage
```

Core design principle:

```text
Parallelize WORKLOADS across machines.
Do not initially distribute ONE MODEL across machines.
```

---

# 1. Machine A — DEV / CONTROL NODE

## Known hardware

| Component         | Specification                            |
| ----------------- | ---------------------------------------- |
| Manufacturer      | Lenovo                                   |
| System model      | 83AA                                     |
| CPU               | AMD Ryzen 7 7840S                        |
| CPU topology      | 8 cores / 16 threads                     |
| Architecture      | Zen 4                                    |
| Integrated GPU    | AMD Radeon 780M                          |
| GPU architecture  | RDNA 3                                   |
| GPU compute units | 12 CUs                                   |
| System memory     | 32GB                                     |
| GPU memory        | Shared system memory, not dedicated VRAM |
| Current OS        | Windows 11 Home 64-bit, Build 26200      |
| Planned OS        | Linux                                    |
| Storage           | Not yet audited                          |

DXDiag currently reports approximately:

```text
Display Memory: ~4GB
Shared Memory: ~14GB
Approx total graphics memory: ~18GB
```

This **does not mean the 780M has 18GB of dedicated VRAM**.

It is an integrated GPU dynamically using the 32GB system memory.

## Initial verdict

### Primary role

**Human-facing development and cluster control plane.**

Run here:

```text
VS Code
terminal
Git
SSH
tmux
Python / uv
Node
Rust/Go/etc.
Codex
Claude Code
OpenCode
browser
project coordination
lightweight Docker
small tests
```

### Secondary role

The Radeon 780M can be used experimentally for:

```text
llama.cpp + Vulkan
small quantized LLMs
embeddings
classification
reranking
cheap background inference
data preprocessing
```

### Do not make this node responsible for

```text
large CUDA workloads
large model training
persistent production services
24/7 databases
large LLM inference as the main inference server
```

The important architectural insight:

```text
Agentic coding does NOT require local frontier-model inference.

DEV NODE
   │
   ├── local files/tools/tests
   │
   └── frontier inference through API
```

Therefore this machine is already adequate as the primary coding workstation.

---

# 2. Machine B — GPU / COMPUTE NODE

## Known hardware

| Component      | Specification                             |
| -------------- | ----------------------------------------- |
| Manufacturer   | ASUS system                               |
| CPU            | Intel Core i5-12400F                      |
| CPU topology   | 6 performance cores / 12 threads          |
| GPU            | NVIDIA GeForce RTX 4060 Ti                |
| Exact board    | RTX 4060 Ti NB DUO 16GB-V                 |
| VRAM           | **16GB dedicated GDDR6**                  |
| System RAM     | 48GB                                      |
| SSD            | Samsung SSD 980 500GB                     |
| Secondary disk | ST2000DM008 2TB                           |
| Current OS     | Windows 11 Enterprise 64-bit, Build 26200 |
| Linux status   | TBD                                       |

Important CPU detail:

```text
i5-12400F
        ↑
        F = no integrated GPU
```

The RTX 4060 Ti therefore serves as both the display GPU and CUDA accelerator.

## Initial verdict

This machine is the **most valuable compute node in the cluster**.

### Primary roles

```text
CUDA
PyTorch
local LLM inference
embeddings
reranking
ML experiments
heavy pytest suites
compilation
Docker builds
document processing
batch jobs
AI dataset generation
evaluation jobs
```

### Local inference architecture

Run an OpenAI-compatible inference server here:

```text
                RTX 4060 Ti 16GB
                       │
              llama.cpp / vLLM
                / Ollama etc.
                       │
                       ▼
              OpenAI-compatible API
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
       DEV node     DEPLOY node    scripts
```

Example conceptual endpoint:

```text
http://gpu-node:8000/v1/
```

All machines can then consume the GPU as a **network AI service**.

### Expected useful model class

16GB VRAM makes this particularly useful for:

```text
7B-class models        → easy
8B-class models        → easy
14B-class quantized    → very useful
larger quantized       → possible with compromises / CPU offload
embedding models       → excellent
rerankers              → excellent
vision encoders        → useful
small QLoRA research   → viable
```

Do not treat it as a replacement for frontier cloud models.

Instead:

```text
Cheap/repetitive intelligence
        ↓
local 4060 Ti

Hard reasoning / huge context
        ↓
frontier cloud model
```

The 48GB system RAM is also valuable for:

```text
CPU offload
dataset processing
large build jobs
multiple containers
model loading
parallel workers
```

## OS decision to investigate

Two reasonable configurations exist.

### Option A — native Linux

Best if this becomes a dedicated compute machine.

Advantages:

```text
simpler CUDA stack
simpler Docker
persistent inference servers
SSH-first operation
better headless behavior
less Windows overhead
```

### Option B — Windows + WSL2

Good if Windows remains needed.

Advantages:

```text
preserves Windows desktop
CUDA works through WSL2
Linux development environment available
```

Potential downside:

```text
more layers
network/service management less clean
reboots affect inference
less ideal as permanent compute appliance
```

Do not reinstall this machine until its actual usage requirements are audited.

---

# 3. Machine C — DEPLOYMENT / DATA / SERVICES NODE

## Known hardware

Hostname observed:

```text
vphk2001-GE62-6QC
```

### Hardware / OS

| Component              | Observed specification       |
| ---------------------- | ---------------------------- |
| CPU                    | Intel Core i5-6300HQ         |
| CPU topology           | 4 cores / 4 threads          |
| Frequency              | 2.30GHz, boost around 3.2GHz |
| RAM                    | ~23.4GiB usable              |
| Swap                   | 48GB                         |
| OS                     | Ubuntu 24.04 64-bit          |
| Kernel shown           | Linux 7.0.0-30-generic       |
| GPU                    | Not yet audited              |
| Root filesystem        | ~467GB                       |
| Other observed mount   | ~931GB                       |
| Research_Wiki mount    | ~1.78TB                      |
| VCIResearchWiki1 mount | ~646GB                       |

These filesystem values are **mount observations**, not yet confirmed physical-drive inventory.

Need to distinguish:

```text
physical disks
partitions
network mounts
bind mounts
external drives
```

before designing storage architecture.

### Existing software/services observed

Processes currently include:

```text
Docker
containerd
Redis
MongoDB
Cloudflare Tunnel
Tailscale
TeamViewer
VS Code
OpenCode
pytest
Python
```

### Current performance state

Observed during screenshot:

```text
CPU usage       ~96.6%
4-core load

1-minute load   ~18.9
5-minute load   ~22.3
15-minute load  ~23.6

RAM used        ~8.8GB / 23.4GB
Swap used       ~8.5GB / 48GB
```

Major CPU consumers included:

```text
OpenCode
VS Code
pytest
Python
```

This strongly suggests that the machine is currently being asked to do too many development/compute jobs.

## Initial verdict

Turn this machine into a **boring, stable server**.

### Primary roles

```text
Docker Compose
PostgreSQL
MongoDB
Redis
APIs
web applications
Cloudflare Tunnel
scheduled jobs
dataset/artifact storage
staging
deployment
possibly container registry
possibly object storage
```

### Remove/offload heavy work

Move to Machine B:

```text
large pytest runs
AI inference
ML workloads
large compilation
large indexing jobs
CPU-heavy agents
Docker image builds
```

Move interactive development to Machine A:

```text
VS Code
OpenCode
Codex
Claude Code
interactive coding
```

Ideal steady-state architecture:

```text
Machine C:
low CPU utilization
predictable memory use
boring services
high uptime
```

Reliability is more important than peak performance here.

---

# 4. Proposed Node Identities

Use simple permanent logical names.

```text
dev
gpu
deploy
```

Possible mapping:

```text
dev     → Ryzen 7840S / 32GB / 780M
gpu     → i5-12400F / 48GB / RTX 4060 Ti 16GB
deploy  → i5-6300HQ / ~24GB / Ubuntu
```

Avoid tying automation to transient IP addresses.

---

# 5. Network Architecture

First choice:

```text
Tailscale
```

Use it for:

```text
node identity
remote access
SSH
private inference APIs
administration
remote deployment
```

Expected interaction:

```bash
ssh dev
ssh gpu
ssh deploy
```

If machines are physically on the same LAN, investigate Ethernet capability.

For bulk transfers:

```text
LAN Ethernet
```

may outperform routing through unnecessary network layers.

Tailscale can remain the **control/network identity plane**.

---

# 6. Source-Code Architecture

## Do NOT share one live working directory between machines

Avoid:

```text
shared NFS project directory
        ↑
   three agents editing
```

Use Git instead.

```text
                    GitHub
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
         dev          gpu       deploy
        clone         clone       clone
```

For concurrent agents use:

```text
Git branches
Git worktrees
commits
pull requests
```

Example:

```text
agent/frontend
agent/backend
agent/tests
agent/data-pipeline
```

This makes Git the coordination protocol.

Shared storage can later be used for:

```text
datasets
artifacts
model weights
backups
logs
```

but **not as the primary multi-agent source-code synchronization mechanism**.

---

# 7. Agentic Coding Architecture

Initial implementation should be deliberately simple.

From `dev`, an agent should eventually be able to invoke tools such as:

```bash
ssh gpu "cd ~/project && uv run pytest"

ssh gpu "cd ~/project && python scripts/build_embeddings.py"

ssh deploy "cd ~/services/project && docker compose up -d"
```

Conceptually expose these capabilities as:

```text
run_local(task)

run_gpu(task)

run_deploy(task)

query_local_model(prompt)

deploy_service(project)
```

Then:

```text
                       AGENT
                         │
                  Task classification
                         │
       ┌─────────────────┼─────────────────┐
       ▼                 ▼                 ▼
    DEV NODE          GPU NODE        DEPLOY NODE
    editing           CUDA            services
    research          LLM             databases
    light tests       heavy tests     staging
```

This is already a useful agentic compute fabric without Kubernetes, Ray or Slurm.

---

# 8. Local AI Routing Idea

Longer term, build a simple inference hierarchy.

```text
Incoming AI task
       │
       ▼
Can a small model solve it?
       │
  ┌────┴────┐
 YES        NO
  │          │
  ▼          ▼
780M      Can 4060 Ti solve it?
             │
        ┌────┴────┐
       YES        NO
        │          │
        ▼          ▼
  RTX 4060 Ti    Cloud frontier model
```

Example allocation:

| Task                   | Preferred compute    |
| ---------------------- | -------------------- |
| Embeddings             | GPU / possibly 780M  |
| Reranking              | GPU                  |
| Simple classification  | Local model          |
| Information extraction | Local model          |
| Document tagging       | Local model          |
| Code indexing          | CPU/GPU worker       |
| Cheap subagent         | Local model          |
| Complex coding         | Cloud frontier model |
| Architecture reasoning | Cloud frontier model |
| Huge-context analysis  | Cloud frontier model |
| CUDA experiment        | RTX 4060 Ti          |

This lets local hardware absorb **volume**, while cloud models provide **intelligence ceiling**.

---

# 9. Important Non-Goal

Do not initially attempt:

```text
780M
 +
4060 Ti
 +
three CPUs
 ↓
ONE distributed LLM
```

Distributed model inference across heterogeneous devices is technically possible in some frameworks, but this hardware combination is badly balanced for it.

Network communication and the weakest device can dominate performance.

Initial principle:

> **Distribute jobs, not tensor operations.**

Example:

```text
GPU node:
model inference

DEV node:
data preprocessing

DEPLOY node:
database queries
```

running simultaneously is useful.

Splitting every transformer layer across all three machines probably is not.

---

# 10. Potential Public Repository Strategy

Do **not** create five repositories immediately.

Start with one umbrella repository:

```text
agentic-homelab
```

Suggested structure:

```text
agentic-homelab/
│
├── README.md
├── docs/
│   ├── architecture.md
│   ├── hardware.md
│   ├── networking.md
│   └── decisions/
│
├── inventory/
│   ├── dev.md
│   ├── gpu.md
│   └── deploy.md
│
├── bootstrap/
│   ├── dev/
│   ├── gpu/
│   └── deploy/
│
├── remote-exec/
│
├── inference/
│   ├── llama-cpp/
│   ├── vllm/
│   └── benchmarks/
│
├── deployment/
│   └── templates/
│
├── scripts/
│
└── benchmarks/
```

Only split repositories once boundaries become real.

Possible future repositories:

```text
agentic-remote-runner
local-llm-gateway
agentic-homelab-infra
```

But **do not split them yet** unless independent codebases emerge.

---

# 11. PUBLIC REPOSITORY SECURITY RULES

This matters because the infrastructure is real.

Never commit:

```text
SSH private keys
Tailscale auth keys
Cloudflare tunnel tokens
API keys
GitHub tokens
database passwords
.env files
production certificates
private service credentials
```

Use:

```text
.env.example
config.example.yaml
HOSTNAME placeholders
secret references
```

instead.

Before every public push:

```text
git diff
git status
secret scan
```

Strongly consider:

```text
gitleaks
```

or equivalent secret scanning.

Also be extremely careful with **GitHub self-hosted Actions runners attached to public repositories**.

An untrusted pull request must not be allowed to execute arbitrary code on a machine containing:

```text
SSH keys
Tailscale access
production credentials
other repositories
personal files
```

If self-hosted runners are later used:

```text
trusted branches/workflows only
isolated runner user/container/VM
minimal credentials
no unrestricted fork PR execution
```

---

# 12. Immediate Task for the Next AI With SSH Access

## PHASE 0 — AUDIT ONLY

Before changing anything, generate a reproducible inventory.

### Linux hosts

Run equivalent commands:

```bash
hostnamectl
uname -a

lscpu
free -h

lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL
df -hT
findmnt

lspci -nn | grep -Ei 'vga|3d|display|ethernet|network'

ip -br address
ip route

docker version
docker info

systemctl --type=service --state=running

ss -tulpn
```

For NVIDIA machine if Linux/WSL:

```bash
nvidia-smi
```

Check disks where appropriate:

```bash
sudo smartctl --scan
```

### Windows machines

Collect equivalent PowerShell inventory:

```powershell
Get-ComputerInfo

Get-CimInstance Win32_Processor

Get-CimInstance Win32_PhysicalMemory

Get-CimInstance Win32_VideoController

Get-CimInstance Win32_DiskDrive

Get-NetAdapter
```

And:

```powershell
nvidia-smi
```

on the RTX system.

Do not assume the screenshots are complete.

---

# 13. Questions the Audit Must Answer

Only five questions matter initially.

### Q1. What are the exact disks and network links?

Need:

```text
SSD/HDD models
capacity
free capacity
mount layout
1GbE / 2.5GbE / Wi-Fi
actual inter-node throughput
```

### Q2. What OS should the RTX 4060 Ti machine use?

Choose between:

```text
native Linux
vs
Windows + WSL2
```

based on actual desktop requirements.

### Q3. Can the RTX node expose a reliable inference API?

Minimum success criterion:

```text
DEV
 │
 │ HTTP
 ▼
GPU
 │
 ▼
local model response
```

### Q4. Can an agent remotely execute tests/builds?

Minimum success criterion:

```text
DEV agent
   ↓
ssh gpu
   ↓
git checkout
   ↓
pytest/build
   ↓
return result
```

### Q5. Can deployment become a separate final step?

Minimum success criterion:

```text
code commit
   ↓
build
   ↓
deploy node
   ↓
docker compose
   ↓
health check
```

---

# 14. First Three Deliverables

Do not install cluster frameworks yet.

## Artifact 1 — Machine inventory

Create:

```text
inventory/dev.md
inventory/gpu.md
inventory/deploy.md
```

containing verified hardware/software/network/storage information.

Commit it.

---

## Artifact 2 — Three-node connectivity

Make these work reliably:

```bash
ssh dev
ssh gpu
ssh deploy
```

Prefer SSH keys + Tailscale/private network.

Document it.

---

## Artifact 3 — One Complete Distributed Workflow

Build one real workflow:

```text
DEV
 │
 │ agent edits code
 ▼
Git
 │
 ▼
GPU
 │
 │ runs heavy tests/build/inference
 ▼
Git / artifact
 │
 ▼
DEPLOY
 │
 │ docker compose
 ▼
running service
```

Do this **before** implementing orchestration software.

---

# 15. Next Brainstorming Directions

Once those three artifacts work, investigate these in this order.

## A. Remote execution abstraction

Instead of agents manually producing:

```bash
ssh gpu "..."
```

build a tiny CLI such as:

```bash
cluster run gpu pytest
cluster run gpu build
cluster run deploy status
cluster deploy research-wiki
cluster model health
```

This could become the first meaningful standalone public project.

---

## B. Local model gateway

Create one stable private interface:

```text
/v1/chat/completions
/v1/embeddings
/v1/models
```

The underlying model engine can then change without modifying every application.

Possible backend experiments:

```text
llama.cpp
vLLM
Ollama
```

Benchmark instead of assuming which is best.

---

## C. Resource-aware agent routing

Eventually expose machine capabilities:

```yaml
dev:
  cpu: 8
  ram_gb: 32
  gpu: amd_780m
  roles:
    - interactive
    - light_cpu

gpu:
  cpu: 6
  threads: 12
  ram_gb: 48
  gpu: rtx_4060_ti_16gb
  roles:
    - cuda
    - llm
    - build
    - heavy_test

deploy:
  cpu: 4
  ram_gb: 24
  roles:
    - database
    - service
    - deployment
    - storage
```

Then agents could choose machines from capability rather than hostname.

---

## D. Shared artifact/data layer

Possible later addition:

```text
MinIO / S3-compatible object storage
```

for:

```text
datasets
model outputs
build artifacts
research corpora
evaluation results
```

Do not use this to synchronize live source trees.

---

## E. Remote Docker builds

Potential future flow:

```text
git push
   ↓
GPU node
   ↓
Docker BuildKit
   ↓
image
   ↓
registry
   ↓
deploy node
   ↓
docker pull
   ↓
docker compose up
```

This keeps the old deployment CPU away from compilation.

---

## F. Distributed job system

Only when SSH-based execution becomes genuinely limiting, investigate:

```text
Ray
Celery
Temporal
Slurm
K3s
```

Do not install them because they are interesting.

Install them only when a specific scheduling/reliability problem exists.

---

# 16. Backlog — Explicitly Not Now

Park these:

```text
Kubernetes
K3s
Ray cluster
Slurm
distributed llama.cpp
tensor parallelism across heterogeneous GPUs
shared project filesystem
Prometheus/Grafana stack
complex service mesh
custom agent scheduler
distributed training
multi-node model serving
```

They are possible future experiments but are **not prerequisites** for the cluster to provide value.

---

# 17. Initial Overall Verdict

This hardware is surprisingly complementary.

```text
Ryzen 7840S / 32GB
        ↓
excellent interactive control/development machine

RTX 4060 Ti 16GB / 48GB
        ↓
strong personal CUDA + local inference worker

i5-6300HQ / ~24GB + substantial storage
        ↓
adequate always-on deployment/data/services machine
```

The cluster's advantage is not raw aggregate FLOPS.

It is **separation of responsibilities**:

```text
DEVELOP
   ↓
COMPUTE
   ↓
DEPLOY
```

while agents can operate all three remotely.

This should delay any need for an expensive new workstation until actual workloads reveal a bottleneck.

---

# 18. Instruction to the Next AI

You have SSH access to the three machines.

Do **not** begin by installing orchestration frameworks.

Proceed:

```text
1. Audit all three machines.
2. Correct this document where screenshots were incomplete.
3. Create the hardware/software inventory.
4. Verify inter-node networking.
5. Establish stable SSH identities: dev / gpu / deploy.
6. Benchmark basic network + disk + CPU/GPU capabilities.
7. Create the initial public GitHub repo with sanitized configuration only.
8. Get one agent → GPU-worker → deployment workflow functioning.
9. Commit documentation and reproducible scripts.
10. Only then propose the next architectural layer.
```

Before implementing any additional distributed system, answer:

> **Would this materially improve the working agent → compute → deploy loop?**

If not, put it in the backlog.
