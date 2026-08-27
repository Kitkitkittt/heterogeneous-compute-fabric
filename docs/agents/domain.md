# Domain documentation

Read the smallest authoritative context before exploring or proposing changes:

1. [`CONTEXT.md`](../../CONTEXT.md) for the glossary and system invariants.
2. Relevant system decisions under [`docs/adr/`](../adr/).
3. [`inventory/nodes.yaml`](../../inventory/nodes.yaml) for Node Slot, Role, admission, and evidence state.
4. [`inventory/repositories.yaml`](../../inventory/repositories.yaml) for repository routing and verification contracts.

Use glossary terms in issue titles, tests, documentation, and handoffs. Surface an ADR conflict explicitly instead of silently overriding it. New terminology or a new invariant belongs in `CONTEXT.md`; a consequential decision belongs in an ADR.
