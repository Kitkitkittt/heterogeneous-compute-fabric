# ADR-0001: Public concept and private implementation planes

Status: accepted

Date: 2026-08-27

## Context

The architecture benefits from public review, but implementation and operations require source code, machine assignments, access mappings, evidence, and configuration that should not be published. Hardware and installations also change more often than architectural responsibilities.

Using hostnames or current hardware as public identities couples the architecture to disposable operational state. Publishing a private repository location would also reveal an unnecessary access target without helping readers understand the concept.

## Decision

1. Keep this repository limited to implementation-neutral architecture, node archetypes, diagrams, terminology, and decisions.
2. Identify conceptual capacity through stable `<purpose>-<ordinal>` Node Slots.
3. Treat hardware assignments and installations as replaceable private state.
4. Keep implementation code, automation, inventory, admission evidence, operational mappings, configuration, and runbooks in access-controlled systems.
5. Do not publish private repository locations or live infrastructure identifiers.
6. Keep secrets outside source control in an approved credential store.

## Consequences

- Public discussion can focus on responsibilities, contracts, boundaries, and trade-offs.
- Reinstalling or replacing a machine does not require public architecture changes.
- The public repository cannot deploy or operate a fabric by itself.
- Authorized operators need separate access to implementation and operations data.
- Examples must remain fictional and must not be updated with live values.

## Rejected alternatives

- **Publish sanitized implementation:** rejected because implementation details still expand the public maintenance and discovery surface.
- **Use hostnames as node identity:** rejected because hostnames are disposable and operational.
- **Publish the private repository location:** rejected because it is unnecessary for understanding the public concept.
- **Keep one public file containing operational detail:** rejected because architecture review does not require live access mappings or evidence.
