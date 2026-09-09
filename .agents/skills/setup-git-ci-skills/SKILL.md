---
name: setup-git-ci-skills
description: "Set up or maintain project-local Git and CI guidance."
disable-model-invocation: true
---

# Set Up Git and CI Skills

Create guidance, not infrastructure. This prompt-driven initializer proposes a complete diff and writes only after approval. It does not install dependencies, alter Git or CI, provision runners, access credentials, publish source, or install itself.

This file and [project-skill.md](./project-skill.md) form the distributable source. Installation means deliberately copying the complete directory into a user-confirmed global skills directory supported by the agent harness. Infer no harness path or cross-harness discovery. Invoke the installed initializer explicitly as `setup-git-ci-skills`.

## 1. Discover

Read [project-skill.md](./project-skill.md) completely; its policy is mandatory seed material. Inspect without mutation:

- root and nested instruction files, their documented hierarchy, and project-local skill layouts;
- Git root, status, worktrees, branches, upstreams, sanitized remotes, history, submodules, Git LFS configuration, tags, and local policy;
- issue ownership, branch/worktree bindings, review destination, integration policy, publication gates, and public/private boundaries;
- CI workflows, events, refs, permissions, concurrency, jobs, runners, required-check documentation, and artifact handling;
- manifests, lockfiles, toolchains, bootstrap instructions, and existing lint, type, test, build, and complete-verification commands;
- relevant installed skills and existing Git, CI, recovery, trust, admission, and agent guidance.

Treat configured guidance as authoritative. Record each command's working directory and prerequisites. Sanitize remote URLs before display or generated guidance by removing embedded tokens, passwords, userinfo, private addresses, and private mappings. Never echo configuration secrets or credential-bearing command output. Report empty projects and unsupported capabilities without inventing commands, providers, remotes, schedulers, or paths.

Stop before proposing writes when instructions materially conflict or required facts remain absent. Ask only the question needed to proceed.

## 2. Establish provenance

Before forming an upgrade or removal diff, search the existing issue or pull-request tracker and Git history for records associated with the initializer's repo-relative target path. A current record contains the generated skill path and full-file SHA-256 digest, the exact pointer line and containing heading, the approved base revision, and a link to the approved diff. Follow an explicit supersedes chain to its current record; multiple unresolved current records stop the run safely.

Names and matching paths do not prove ownership. No valid current record means preserve existing content and request explicit ownership confirmation before changing it. Adopted content remains user-owned unless explicitly transferred. An unchanged rerun performs no writes regardless of missing provenance; provenance gates only proposed changes and removal. Add no manifest or configuration store.

## 3. Propose

Adapt the mandatory seed to discovered, approved facts. Adopt existing guidance by reference rather than duplication. Keep one project-local skill under the existing layout. When no layout exists, ask the user to choose a supported project-local location.

Select a root instruction target as follows:

- If one of `AGENTS.md` or `CLAUDE.md` exists, follow that file and its repository hierarchy.
- If both exist, preserve their hierarchy and ask the user which file should receive the pointer when the authoritative target is not explicit.
- If neither exists, ask which supported instruction file to create.

Add one conditional pointer, tailored to the approved skill name and path:

```markdown
For Git ownership, CI verification, source recovery, or publication work, load the project-local `project-git-ci` skill at `.agents/skills/project-git-ci/SKILL.md`.
```

The initializer remains explicit user-invoked setup. The project skill remains model-invoked through its conditional description and instruction pointer.

Show one complete proposed diff before any write. Identify new content and pre-existing content proposed for adoption. Include the exact post-write provenance tracker comment or update in the proposal. Bind approval to the full diff and base revision. Explain unsupported capabilities and omissions, then obtain explicit approval for that diff, revision, and tracker update. Tracker publication requires explicit permission and never includes commits or pushes.

## 4. Apply

Before each write, verify that `HEAD` still equals the approved base revision and re-read the target plus every not-yet-written target against the approved diff. A changed revision, target, or assumption stops before the next write and requires a new full diff and approval.

For first setup, create only the approved skill and pointer. An unchanged rerun makes no changes. For upgrade or removal, alter only bytes established as initializer-owned by valid provenance and still matching their recorded identity. Preserve human edits and unrelated sections. Removal deletes only the recorded full skill file and exact pointer line under its recorded heading.

Writes are individual, not atomic. On partial failure, report each file as written, unchanged, or failed. Offer to restore only initializer-owned bytes written by this invocation whose post-write bytes remain unchanged, and restore them only with approval. Never overwrite concurrent edits.

## 5. Verify and record

Re-read changed files, resolve local links, validate frontmatter, and confirm the root pointer conditionally triggers the project skill while setup remains explicit. Approval of CI execution expires when the source revision or executable workflow changes.

After successful verification and with publication permission, record the approved post-write provenance in the selected issue or pull request: generated skill path and SHA-256 digest, exact pointer heading and line, approved revision and diff link, and the previous record it supersedes. For removal, record a tombstone stating that no current initializer-owned bytes remain. If this tracker update fails, stop, report the exact written and unrecorded state, and do not claim success.

Report the exact diff and checks run. Structural checks confirm document shape and required wording only; prompt instructions are neither a deterministic installer nor proof of runtime isolation or behavioral compliance.
