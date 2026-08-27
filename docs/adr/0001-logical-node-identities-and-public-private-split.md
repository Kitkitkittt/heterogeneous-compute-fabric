# ADR-0001: Stable node slots and a private operations overlay

Status: accepted

Date: 2026-08-27

## Context

Physical machines will be reinstalled and their hardware may be upgraded or replaced. The repository is public, while operational access requires hostnames, addresses, SSH users, owners, recovery locations, and credentials that must not be published.

Using current hostnames as architecture identifiers couples issues and runbooks to disposable installation state. Publishing all operational mappings would also make a public documentation repository an unnecessary infrastructure-discovery surface.

## Decision

1. Identify capacity through stable `<purpose>-<ordinal>` Node Slots such as `dev-01` and `compute-01`.
2. Treat hardware as a replaceable assignment and the operating system as a disposable installation.
3. Store sanitized capacity, evidence, roles, and gates in the public registry.
4. Store current network identities, SSH users, service ownership, recovery locations, and credential references in a separate private operations overlay.
5. Keep secrets outside both repositories in an approved credential store.
6. Use issue labels of the form `node:<node-id>` to describe task suitability; a task may target more than one node.

## Consequences

- Reinstalling a node does not rename issues, documentation, or workload contracts.
- Hardware can be swapped while preserving a role-oriented Node Slot.
- Agents need access to both the public registry and an authorized private overlay to connect to machines.
- Bootstrap logic must select an explicit OS Profile rather than assuming all Linux distributions are identical.
- Adding a new purpose creates a new series, for example `storage-01`, `gateway-01`, or `backup-01`.

## Rejected alternatives

- **Hostname as node identity:** rejected because hostnames are disposable and private.
- **One public file containing every operational detail:** rejected because public capacity documentation does not require live access mappings.
- **Role-only names without ordinals:** rejected because the fabric is expected to gain multiple nodes with the same purpose.

