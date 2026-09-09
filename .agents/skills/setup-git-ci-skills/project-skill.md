---
name: project-git-ci
description: "Use when work involves Git ownership, branches or worktrees, CI verification, source recovery, publication, or trust boundaries in this project."
---

# Project Git and CI

Adapt this seed only from discovered, approved project facts. Preserve every section. Mark unsupported or unknown capabilities and name the safe next gate rather than removing security or recovery guidance or inventing values. Keep secrets, credentials, private remote locations, access identities, and private mappings out of this file. Sanitize remote URLs by removing tokens, passwords, and userinfo before recording them; never echo configuration secrets.

## Ownership and publication

Name one authoritative source and review destination using public-safe identifiers. Each writer uses an issue-owned branch and isolated worktree under the project's existing direct or integration policy. Publishing requires explicit permission and preserves public/private boundaries. When unsupported or unknown, state that status and set explicit owner confirmation as the safe next gate before writes or publication.

## Verification

List only discovered bootstrap, lint, typing, test, build, and aggregate commands, in required order, with working directory, locked-toolchain prerequisites, timeout expectations, and the command that constitutes complete verification. Evidence records the source commit and each command's exit status. Fabric validation alone is not complete project verification. When unsupported or unknown, state the missing evidence and set maintainer-confirmed commands as the safe next gate before claiming verification.

## CI trust

Name the existing CI adapter and its authoritative workflow files, supported events and refs, least-privilege permissions, reporting, required checks, and safe concurrency behavior. Recommend duplicate-run cancellation only when mandatory evidence remains available. New tools, providers, schedulers, or private runners require measured unmet criteria and existing pilot gates.

Only approved internal jobs run. Approval binds the source revision and executable workflow and expires when either changes. Treat changed or agent-authored code as untrusted pending approval. Prefer existing hosted execution. Private compute requires explicit authorization, disposable isolation, short-lived least-privilege credentials, bounded network, cache and artifact trust, cleanup, and applicable admission evidence. A container or node label is not authorization. When unsupported or unknown, retain this boundary and set explicit owner authorization plus reviewable isolation evidence as the safe next gate; do not delete this section.

## Source recovery

Inventory required refs and tags, Git LFS objects, and submodules. Distinguish retained backups from live mirrors. Name owner-approved loss and recovery targets, destinations, and restore evidence without exposing private mappings. Initialization selects or configures no destination. Mirrors do not recover the GitHub issue control plane. When unsupported or unknown, retain the gap and set owner-approved targets, destination selection, and a demonstrated restore as the safe next gate. Do not claim recoverability without restore evidence; do not delete this section.
