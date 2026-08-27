# Private operations overlay

## Purpose

The public registry answers: **which Node Slot has the right durable capability?**

The private overlay answers: **how does an authorized operator connect, who owns the current state, and how is it recovered?**

## Location

Use a separately access-controlled private repository. `inventory/private.example.yaml` is a structure example only. A populated `inventory/private.yaml` is ignored as an additional guardrail, but an untracked file in a public clone is not the preferred authority.

## Required fields per Node Slot

- current hostname and private-network name/address;
- SSH user and authorized public-key identity references;
- hardware assignment owner and installation owner;
- services and data owners;
- backup, recovery, and rollback locations;
- private repository access class and remote mapping;
- last connectivity and recovery checks;
- timestamped load, free-memory, disk-headroom, temperature, and listener snapshots when needed.

## Never store

- private keys, passwords, tokens, recovery codes, or raw environment files;
- cloud secret keys or tunnel credentials;
- database credentials or production certificates;
- personal filesystem paths unrelated to the fabric.

Store secret values in a password manager or operating-system credential store. The overlay records only a reference that an authorized human can resolve.

## Join contract

The join key is exactly `node_id`. Every private record must match a Node Slot in `inventory/nodes.yaml`. Do not create a second public name or copy private identifiers into public issues.

## Freshness

Every operational observation must include `observed_at` and an owner. Treat live utilization as a short-lived snapshot, not durable capacity. Reinstalling a node invalidates its hostname, host keys, packages, drivers, service state, and connectivity evidence until reverified.

