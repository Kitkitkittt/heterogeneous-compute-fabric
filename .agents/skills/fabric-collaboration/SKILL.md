---
name: fabric-collaboration
description: Coordinate work across heterogeneous compute nodes when a task must be claimed, routed, executed by one or more agents, handed off, admitted, or deployed. Use for cross-node planning and execution; skip ordinary single-worktree edits that do not use the compute fabric.
---

# Fabric collaboration

Produce one traceable GitHub work graph whose source and outputs can move between Node Slots without sharing a mutable checkout or publishing operational identities.

## Workflow

1. **Orient.** Read `CONTEXT.md`, the assigned issue with comments and dependencies, the matching Repository Contract in `inventory/repositories.yaml`, and any ADR touching the task. The step is complete when the intended outcome, authority boundary, blockers, and required evidence are explicit.
2. **Claim.** Assign the issue before the first mutation. Confirm its `### Worktree binding` names one branch, base, and role. For parallel work, use a parent integration issue and independently mergeable child issues with declared ownership and integration order. Read `docs/agents/issue-tracker.md` for the project contract.
3. **Route.** Treat `node:*` labels as candidate locations. Use `fabric route` and current admission evidence to select a Node Slot whose architecture and admitted Roles satisfy the Repository Contract. When no node qualifies, report the failed gate and leave execution blocked instead of bypassing admission.
4. **Isolate.** Give every active writer a separate issue-owned branch and linked worktree. Keep operational mappings outside the public checkout. Read `docs/runbooks/private-operations-overlay.md` only when authorized connection data is required.
5. **Execute and transfer.** Keep commits reviewable and run the repository verification command. Move source between nodes through pushed commits. Move build, model, report, or deployment output as an immutable artifact with a digest and source commit.
6. **Handoff.** Publish the public-safe handoff record from `docs/agents/collaboration.md`. It must identify the issue, Node Slot, branch, source commit, verification, immutable outputs, blockers, next actor, and authority boundary without connection details.
7. **Complete.** Merge into the declared base, close the owning issue, prove the branch has no unique unmerged commits, then remove its clean worktree without force. A live node or Role changes to `schedulable` only through the admission report defined by `docs/runbooks/reinstall-and-admit-node.md`.

## Completion criterion

Every mutation has one owning issue and branch; every execution target passed routing; every cross-node transfer is a commit or immutable artifact; every handoff names the next gate; and no public artifact contains Private Operations Overlay values.
