# Fabric CLI

The `fabric` command is the public seam for validation, routing, private-overlay joins, admission reports, GitHub frontier inspection, and deterministic pilot evidence. Commands fail closed and return a non-zero exit code when their requested outcome is unavailable.

Install the locked environment:

```powershell
uv sync
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

Matches identify only the public file and category. The private pattern is never repeated.

## Route work

```powershell
uv run fabric route `
  --root . `
  --repository heterogeneous-compute-fabric `
  --architecture x86_64 `
  --role cpu-build
```

Routing requires the Repository Contract, Node Slot architecture, node Admission State, declared Role, and per-Role admission state to pass. A listed Role is not automatically schedulable.

## Validate a Private Operations Overlay

```powershell
uv run fabric overlay validate `
  --root . `
  --overlay PATH_TO_PRIVATE_OVERLAY
```

The populated overlay must live outside this public repository. Default output contains only Node Slot join status and credential-reference counts. Raw secret fields are rejected.

## Generate an admission report

Verification agents collect an observation bundle using the contract in the reinstall runbook and then evaluate it:

```powershell
uv run fabric admission report `
  --profile compute-01 `
  --observations PATH_TO_OBSERVATIONS `
  --view public
```

Use `--profile dev-01` for the workstation. The default `public` view never includes `private_evidence`. `--view private` is an explicit operator action and its output must stay in the Private Operations Overlay workflow.

The command can admit CPU/RAM Roles while keeping CUDA gated, or keep a Pop!_OS workstation gated until its profile-specific policies pass.

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
  --artifact PATH_TO_IMMUTABLE_RESULT `
  --health-evidence PATH_TO_HEALTH_EVIDENCE `
  --rollback-evidence PATH_TO_ROLLBACK_EVIDENCE `
  --receipt PATH_TO_RECEIPT `
  --deployment-authorized
```

Without `--deployment-authorized`, the command fails before writing a receipt. The receipt contains hashes and routing evidence, not the evidence-file contents. Real-machine pilot acceptance remains blocked until the live admission issues pass.

## Development checks

```powershell
uv run pytest
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy src
uv run fabric validate --root .
```

