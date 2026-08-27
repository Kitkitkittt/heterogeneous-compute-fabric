# Triage labels

Actor readiness and node suitability are separate signals.

| Canonical label | Meaning |
| --- | --- |
| `needs-triage` | A maintainer must evaluate scope or ownership. |
| `needs-info` | Reporter or operator information is required. |
| `ready-for-agent` | Fully specified, authorized agent work is on the unblocked frontier. |
| `ready-for-human` | A human action or authority is required. |
| `wontfix` | The issue will not be actioned. |

Apply at most one actor-readiness label to an actionable issue. A blocked issue carries dependencies instead of a ready label. Apply any number of `node:<node-id>` labels to describe suitable execution locations; those labels do not prove admission or assign ownership.
