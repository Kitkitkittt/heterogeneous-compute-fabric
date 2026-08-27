# GitHub task routing

GitHub carries three independent workflow signals.

## 1. Node suitability

Use one or more labels of the form `node:<node-id>`:

| Label | Current purpose |
| --- | --- |
| `node:dev-01` | Interactive development, control, and short local tests |
| `node:compute-01` | x86 CPU/RAM builds, CUDA, inference, and batch work |
| `node:cloud-01` | Architecture-compatible bounded ARM64 work |
| `node:deploy-01` | Authorized deployment, persistent-service, database, and storage work |

These labels answer **where could this task run?** A task may name several suitable nodes. They do not prove that a node is currently admitted or reachable.

## 2. Actor readiness

Use exactly one canonical triage state when an issue is on the actionable frontier:

- `needs-triage`: maintainer evaluation required;
- `needs-info`: reporter or operator information required;
- `ready-for-agent`: fully specified and safe for an agent;
- `ready-for-human`: requires human action or authority;
- `wontfix`: intentionally not actioned.

Do not apply a ready label while the issue has an open blocker.

## 3. Dependency readiness

Use native GitHub issue dependencies for ordering. The current reinstall pattern is:

```text
#3 compute-01 human reinstall
  -> #4 compute-01 agent verification
    -> #5 dev-01 human reinstall
      -> #6 dev-01 agent verification
```

When a blocker closes, triage the newly unblocked issue and apply its appropriate ready label. Dependencies establish order; labels identify the next actor.

## Node admission is separate

`inventory/nodes.yaml` is authoritative for `inventoried`, `install_pending`, `installed`, `verified`, `schedulable`, `drained`, and `retired`.

An issue may be ready for an agent while its target node is not schedulable—for example, the issue may exist specifically to verify and admit that node.
