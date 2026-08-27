# Cross-node agent collaboration

This protocol lets multiple agents work across any number of Node Slots without coupling coordination to a hostname, operating system, or shared checkout.

## Four planes

| Plane | Source of truth | Carries |
| --- | --- | --- |
| Control | GitHub Issues, dependencies, assignees, and pull requests | Intent, ownership, blockers, review, completion |
| Work | One issue-owned branch in one isolated worktree per writer | Mutable source for one accountable task |
| Transfer | Git commits and immutable, hashed artifacts | Source and outputs moving between nodes |
| Access | Private Operations Overlay and credential store | Host mappings, SSH users, owners, endpoints, recovery locations, credential references |

The Public Registry identifies capabilities. The Access plane resolves how an authorized operator reaches them. Neither substitutes for the other.

## Collaboration lifecycle

| Stage | Required result |
| --- | --- |
| Discover | Read the issue, domain context, Repository Contract, blockers, and evidence requirements. |
| Claim | One accountable assignee and one machine-readable branch binding exist before mutation. |
| Route | The selected Node Slot satisfies architecture, required Roles, admission evidence, and task authority. |
| Prepare | The writer has an isolated linked worktree; shared interfaces and file ownership are declared for parallel work. |
| Execute | Changes stay within issue scope and verification runs on the immutable source commit. |
| Publish | Commits are pushed; outputs carry a digest, source commit, and verification evidence. |
| Handoff | The issue or PR records current state, blockers, next actor, and authority boundary. |
| Release | The intended base contains the change, the issue is closed, and the clean worktree has no unique commits before removal. |

## Ownership and parallelism

- One issue has one accountable assignee at a time. Reassignment is an explicit handoff, not concurrent ownership.
- One active writer owns one branch and linked worktree. Multiple read-only agents may inspect it.
- Partition parallel work by independently reviewable output. The parent issue defines shared interfaces, file ownership, dependencies, and integration order before child work begins.
- Use native dependencies only when one result is a real prerequisite. Use assignees for ownership and `node:*` labels for candidate execution locations.
- An integrator consumes reviewed commits from child branches. Integrators do not edit a worker's mutable checkout.

Multiple agents may run on one Node Slot, and one workflow may visit several Node Slots, as long as branch ownership and immutable transfer rules remain intact.

## Admission-aware routing

Node suitability, current admission, and task ownership are independent:

1. `node:<node-id>` labels describe where the task could run.
2. `inventory/nodes.yaml` and direct dated evidence describe which Node and Roles are currently schedulable.
3. The Repository Contract describes architecture, Roles, eligible Node Slots, bootstrap, and verification.
4. `fabric route` intersects those contracts. An empty result is a blocker, not permission to select a node manually.

Adding a Node Slot requires a new stable ID, task label, hardware/evidence record, Role admission state, and private mapping. Existing issues, Role Profiles, and collaboration rules remain unchanged.

## Public handoff record

Publish this record as an issue or PR comment. Omit fields that do not apply; never add access-plane values.

```markdown
### Cross-node handoff

- Issue: #<number>
- Status: ready-for-review | blocked | ready-for-next-worker | complete
- Node Slot: <stable-node-id>
- Branch / base: <issue-branch> -> <declared-base>
- Source commit: <full-commit-id>
- Immutable outputs: <artifact-id and sha256, or none>
- Verification: <commands and result>
- Evidence updated: <public-safe references and evidence lifetime>
- Blockers: <issue numbers or failed admission gates>
- Next actor: <human | agent | integrator | operator>
- Authority boundary: <important actions not granted by this handoff>
```

A handoff is complete when the next actor can continue from GitHub plus the Public Registry and needs private data only to establish an authorized connection.

## Failure and recovery

- A worker failure leaves pushed commits and issue evidence intact. The next worker creates or reuses the bound worktree from the pushed branch.
- A node failure changes routing, not task identity. Re-run routing and record the failed gate or choose another eligible, admitted Node Slot.
- A stale installation or snapshot invalidates only evidence with that lifetime. Chassis evidence survives reinstall unless hardware changed.
- A failed integration stays on its issue branch. Recover with a follow-up or revert commit and preserve the original evidence trail.
- Destructive node work, live deployment, and Git history rewriting each require their own explicit authority; a general cross-node handoff does not grant it.

## Fresh-node bootstrap

From a fresh clone:

```powershell
uv sync
npm ci
uv run fabric validate --root . --format json
```

Then read the assigned GitHub issue and invoke the repo-local `fabric-collaboration` skill for any routed or cross-node workflow.
