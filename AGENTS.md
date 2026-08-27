# Agent operating contract

Read [CONTEXT.md](CONTEXT.md) before naming fabric concepts. For cross-node work, task routing, admission, deployment, or an agent-to-agent handoff, use the repo-local [`fabric-collaboration`](.agents/skills/fabric-collaboration/SKILL.md) skill.

## Always

- Treat GitHub Issues as the work control plane. Claim an issue before the first mutation and use its branch binding, blockers, and acceptance evidence.
- Use stable Node Slot IDs in public artifacts. Resolve hostnames, addresses, SSH users, owners, and credential references only through the Private Operations Overlay.
- Give each active writer an issue-owned branch and isolated worktree. Transfer source through commits and outputs through immutable, hashed artifacts.
- Treat `node:*` labels as suitability hints. Route only through Repository Contracts and directly verified admission evidence.
- Run `uv run fabric validate --root . --format json` before publishing a handoff or pull request.

## Context pointers

- Issue creation, ownership, branch binding, dependencies, and completion: [issue tracker](docs/agents/issue-tracker.md).
- Cross-node ownership, parallel work, handoffs, and recovery: [collaboration protocol](docs/agents/collaboration.md).
- Canonical actor-readiness labels: [triage labels](docs/agents/triage-labels.md).
- Domain reading order and terminology: [domain docs](docs/agents/domain.md).
- Candidate-node labels and admission-aware routing: [task routing](docs/task-routing.md).
- Reinstall or admission work: [reinstall and admission runbook](docs/runbooks/reinstall-and-admit-node.md).
- Connection mapping or other operational identities: [private overlay contract](docs/runbooks/private-operations-overlay.md).
