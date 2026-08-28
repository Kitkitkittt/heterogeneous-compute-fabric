# ADR-0001: Public concept and private implementation planes

Status: accepted

Date: 2026-08-27

## Context

The architecture benefits from public review, but implementation and operations require source code, machine assignments, access mappings, evidence, and configuration that should not be published. Hardware and installations also change more often than architectural responsibilities.

Using hostnames or current hardware as public identities couples the architecture to disposable operational state. Publishing a private repository location would also reveal an unnecessary access target without helping readers understand the concept.

## Decision

1. Keep this repository limited to architecture, node archetypes, sanitized hardware summaries, diagrams, terminology, and decisions.
2. Identify capacity through stable `<purpose>-<ordinal>` Node Slots.
3. Permit public CPU, memory, accelerator, storage, role, and broad admission summaries when they contain no access or live operational data.
4. Treat hardware assignments and installations as replaceable state rather than logical identity.
5. Keep implementation code, automation, authoritative inventory, admission evidence, operational mappings, configuration, and runbooks in access-controlled systems.
6. Do not publish private repository locations, hostnames, addresses, users, credentials, API keys, services, access paths, recovery data, or live infrastructure identifiers.
7. Keep secrets outside source control in an approved credential store.

## Consequences

- Public discussion can compare responsibilities, capacity, contracts, boundaries, and trade-offs.
- Reinstalling or replacing a machine updates its sanitized capacity summary without changing Node Slot identity.
- The public repository cannot deploy or operate a fabric by itself.
- Authorized operators need separate access to implementation and operations data.
- Public capacity can support planning but does not prove admission, availability, or benchmark performance.

## Rejected alternatives

- **Publish sanitized implementation:** rejected because implementation details still expand the public maintenance and discovery surface.
- **Hide all hardware capacity:** rejected because sanitized CPU, memory, accelerator, and storage facts improve architecture planning without revealing access paths.
- **Use hostnames as node identity:** rejected because hostnames are disposable and operational.
- **Publish the private repository location:** rejected because it is unnecessary for understanding the public concept.
- **Keep one public file containing operational detail:** rejected because architecture review does not require live access mappings or evidence.
