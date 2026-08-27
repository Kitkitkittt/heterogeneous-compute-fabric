# Fabric CLI

The `fabric` command is the public seam for validation, routing, private-overlay joins, admission reports, GitHub frontier inspection, and deterministic pilot evidence. Commands fail closed and return a non-zero exit code when their requested outcome is unavailable.

Install the locked Python and diagram-rendering environments:

```powershell
uv sync
npm ci
```

Add `--format json` to any command below for stable automation output.

## Validate the Public Registry

```powershell
uv run fabric validate --root .
```

An authorized operator may keep a newline-delimited private pattern set outside the repository:

```powershell
uv run fabric validate --root . --prohibited-patterns PATH_TO_PRIVATE_PATTERN_FILE
```

Matches identify only the public file and category. The private pattern is never repeated. The validator also checks complete Repository Contracts, required hardware evidence, real ISO evidence dates for schedulable nodes and Roles, local links, actual rendering with the pinned Mermaid CLI, source/SVG/PNG manifest hashes, rendered dimensions, and generated text artifacts. Mermaid source hashes use canonical LF line endings so the same commit validates from LF and CRLF Git checkouts; committed SVG and PNG hashes remain exact-byte checks.

## Route work

```powershell
uv run fabric route `
  --root . `
  --repository heterogeneous-compute-fabric `
  --architecture x86_64 `
  --role cpu-build
```

Routing requires the Repository Contract, Node Slot architecture, node Admission State, declared Role, and per-Role admission state to pass. Node, Role, and architecture evidence must each be directly `verified`; `inherited` and `unknown` remain fail-closed. A listed Role is not automatically schedulable.

## Validate a Private Operations Overlay

```powershell
uv run fabric overlay validate `
  --root . `
  --overlay PATH_TO_PRIVATE_OVERLAY
```

The populated overlay must live outside this public repository. Default output contains only Node Slot join status and credential-reference counts. Raw secret fields and bare credential values are rejected; references use credential-store URIs such as `vault://...`.

## Collect admission observations

On the target Linux installation, collect through the bounded, non-configuring local adapter:

```bash
uv run fabric admission collect \
  --node-id compute-01 \
  --role-profile compute \
  --os-profile ubuntu24 \
  --probe-cwd /path/to/issue-worktree \
  --probe-config /private/path/probe-config.yaml \
  --output /private/path/compute-observations.json
```

The private probe configuration supplies a peer target and SSH destination from the Private Operations Overlay. The network gate requires a peer ping, a successful key-only SSH login, and key-only daemon policy. Use `--role-profile workstation` for DEV. The collector does not install packages or change configuration. It performs SMART disk-health checks, bounded CPU, memory, host-GPU, and `--pull=never --rm` GPU-container execution where those gates apply, plus declared inspection commands. Browser acceleration is checked through Chromium's GPU diagnostic page, separately from the OpenGL graphics smoke test. Command output is written as `private_evidence`; stdout reports counts only. Zero exit status alone is insufficient: each probe output must satisfy its named semantic contract. Unsupported, unavailable, timed-out, or semantically incomplete probes remain gated. The `fixture` adapter and `--probe-results` exist for deterministic tests and do not contact a machine.

`profile_upgrade_path` is intentionally manual-only for `pop24`; the collector emits `unknown`. Before evaluation, a human reviews the versioned Pop!_OS upgrade/recovery guidance, records the reviewed source and date in `private_evidence`, and changes only that check to `pass`. Without that handoff every Pop!_OS workstation Role stays gated.

## Generate an admission report

Verification agents collect an observation bundle using the contract in the reinstall runbook and then evaluate it:

```powershell
uv run fabric admission report `
  --node-id compute-01 `
  --role-profile compute `
  --os-profile ubuntu24 `
  --observations PATH_TO_OBSERVATIONS `
  --view public
```

Node Slot, reusable Role profile, and OS Profile are separate inputs. A future `compute-02` can reuse `--role-profile compute`; a workstation uses `--role-profile workstation`. The default `public` view emits only controlled check/status summaries, never caller-authored evidence or `private_evidence`; obvious private identity in a public-evidence input is also rejected. `--view private` is an explicit operator action and its output must stay in the Private Operations Overlay workflow.

CPU execution, memory execution, and CUDA are independent gates. The command can admit CPU work while keeping RAM and CUDA gated, or keep a Pop!_OS workstation gated until its profile-specific policies pass.

## Report the GitHub frontier

Live read-only GitHub query:

```powershell
uv run fabric frontier `
  --root . `
  --repository Kitkitkittt/heterogeneous-compute-fabric
```

Deterministic fixture or exported issue data:

```powershell
uv run fabric frontier --root . --issues-file PATH_TO_ISSUES_JSON
```

The report includes only open, unassigned, unblocked issues. It keeps task suitability (`node:*`) separate from current node admission.

## Record a deterministic pilot

The v1 adapter records evidence; it never deploys to a real node:

```powershell
uv run fabric pilot `
  --root . `
  --request PATH_TO_PILOT_REQUEST `
  --issue-repository Kitkitkittt/heterogeneous-compute-fabric `
  --worktree PATH_TO_LINKED_ISSUE_WORKTREE `
  --artifact PATH_TO_IMMUTABLE_RESULT `
  --review-evidence PATH_TO_REVIEW_JSON `
  --test-evidence PATH_TO_TEST_JSON `
  --health-evidence PATH_TO_HEALTH_EVIDENCE `
  --rollback-evidence PATH_TO_ROLLBACK_EVIDENCE `
  --receipt PATH_TO_RECEIPT `
  --deployment-authorized
```

The live verifier confirms the issue number embedded in the branch is open in the selected GitHub repository. The selected worktree's normalized `origin` must resolve to that same repository. Deterministic tests may use `--issue-evidence` instead. The selected path must be a clean, registered linked worktree whose current issue branch and `HEAD` exactly match the request. Review, test, health, and rollback JSON each require `status: pass` and the same source commit. Without `--deployment-authorized`, the command fails before writing a receipt. The receipt contains hashes and verification results, not local paths or evidence-file contents. Real-machine pilot acceptance remains blocked until the live admission issues pass.

## Development checks

```powershell
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run fabric validate --root .
```
