---
name: setup-git-ci-skills
description: "Discover a project's Git and CI contracts, then propose tailored project-local agent guidance. Run explicitly to initialize, upgrade, or remove that guidance."
disable-model-invocation: true
---

# Set Up Git and CI Skills

Create guidance, not infrastructure. This prompt-driven initializer inspects a project, proposes a complete diff, and writes only after approval. It never installs dependencies, changes Git or CI, provisions runners, accesses credentials, publishes source, or installs itself globally.

The directory containing this file and [project-skill.md](./project-skill.md) is distributable source. It becomes installed only when the complete directory is deliberately copied into a user-confirmed global skills directory supported by that agent harness. Do not infer the directory or promise discovery across harnesses. Invoke the installed initializer explicitly as `setup-git-ci-skills`.

## 1. Discover

Read the repository's instruction files and local skill layout. Inspect, without mutation:

- Git root, status, worktrees, branches, upstreams, remotes, submodules, Git LFS configuration, tags, and repository-local Git policy;
- issue ownership, branch/worktree bindings, review destination, integration policy, publication gates, and public/private boundaries;
- CI workflow definitions, events, refs, permissions, concurrency, jobs, runners, required-check documentation, and artifact handling;
- manifests, lockfiles, toolchain files, bootstrap instructions, and existing lint, type, test, build, and complete-verification commands;
- relevant installed skills and existing project-local Git, CI, recovery, trust, admission, and agent guidance.

Treat configured guidance as authoritative. Record each command's working directory and prerequisites. Sanitize remote URLs before display or generated guidance by removing embedded tokens, passwords, userinfo, private addresses, and private mappings. Never echo configuration secrets or credential-bearing command output. If the project is empty or a capability is unsupported, say so rather than inventing a command, provider, remote, scheduler, or agent installation path.

## 2. Reconcile

Adopt existing guidance by reference instead of duplicating it. Preserve these contracts unless a stricter project rule controls them:

- One authoritative source and review destination per project. Each writer uses an issue-owned branch and isolated worktree under the project's direct or integration policy. Publishing requires explicit permission.
- Source recovery inventories required refs and tags, Git LFS objects, and submodules. It distinguishes retained backups from live mirrors. Recoverability requires owner-approved loss and recovery targets plus restore evidence. Initialization selects and configures no backup destination. Git mirroring does not recover the GitHub issue control plane.
- Complete verification reuses discovered bootstrap, lint, typing, tests, build, and aggregate commands. Fabric validation alone is not complete verification. Evidence retains toolchain and locked-dependency prerequisites, working directory, exit status, timeout, and source commit.
- CI adapters own event and ref selection, least-privilege permissions, result reporting, and required checks. Recommend duplicate-run cancellation only when mandatory evidence remains available. Add a tool, provider, scheduler, or private runner only against measured unmet criteria and existing pilot gates.
- Only approved internal jobs run. Approval binds both source revision and executable workflow and expires when either changes. Agent-authored code is untrusted until approved. Prefer existing hosted execution. Private compute requires explicit authorization, disposable isolation, least-privilege short-lived credentials, bounded network, cache, and artifact trust, cleanup, and applicable admission evidence. Containers and node labels describe placement, not authorization.

Stop before proposing writes when instructions materially conflict or required facts remain absent. Ask only the question needed to resolve the conflict or fact.

## 3. Propose

Use [project-skill.md](./project-skill.md) as seed material, adapting it to facts found in the project. Keep policy in one project-local skill under the existing local skill layout. When no layout exists, ask the user to choose a supported project-local location; assume no harness path.

Add one conditional pointer to the existing root instruction file. Tailor this concrete shape to the project skill's actual name and path:

```markdown
For Git ownership, CI verification, source recovery, or publication work, load the project-local `project-git-ci` skill at `.agents/skills/project-git-ci/SKILL.md`.
```

The initializer remains explicit setup invoked by the user. The installed project skill remains model-invoked through its conditional description and instruction pointer.

Show one complete proposed diff before any write. Identify newly created content and any pre-existing content proposed for adoption. Names and matching paths do not prove ownership. Bind approval to the full diff and source revision. Record durable provenance for generated content in the existing issue or pull-request control plane as a reference to the approved diff plus the exact generated-content identity or digest; add no manifest. Missing provenance defaults to preserving content and requesting explicit ownership confirmation, never inferred ownership. Explain unsupported capabilities and deliberate omissions. Obtain explicit approval for the diff and revision.

## 4. Apply

After approval, re-read every target and compare it with the version used for the proposal. Before each write, recheck that target and all not-yet-written targets; concurrent edits or changed assumptions stop the run before the next write.

For first setup, create only the approved project-local skill and pointer. An unchanged rerun makes no changes. For an upgrade, preserve human edits and unrelated sections; show and obtain approval for the exact initializer-owned diff. For removal, show and obtain approval for deleting only bytes whose provenance identifies this initializer and whose current bytes still match. Adopted files and pointers remain user-owned unless the user explicitly transfers ownership. A conflict with existing or human-edited guidance stops the run rather than overwriting it.

Write files individually and never claim atomic multi-file writes. On partial failure, report each file as written, unchanged, or failed. Offer to restore only initializer-owned bytes written by this invocation whose post-write bytes remain unchanged, and restore them only with approval. Never overwrite a concurrent edit.

## 5. Verify

Re-read changed files, resolve every local link, validate skill frontmatter, and confirm the root pointer conditionally triggers the project skill while setup remains explicit. Report the exact diff and checks run. State that structural checks confirm document shape and required wording only; prompt instructions are neither a deterministic installer nor proof of runtime isolation or behavioral compliance.
