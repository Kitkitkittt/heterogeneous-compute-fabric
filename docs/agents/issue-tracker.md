# GitHub issue control plane

Issues and specifications live in `Kitkitkittt/heterogeneous-compute-fabric`. Run `gh` inside the clone so the remote selects the repository.

## Ownership contract

- Create or reuse an issue before a mutation.
- Assign one accountable owner when work begins.
- Record true prerequisites as native issue dependencies.
- Put this machine-readable block under `### Worktree binding`:

```json
{"branch":"codex/<issue>-<slug>","base":"main","role":"direct"}
```

Valid roles are `direct`, `integration`, and `leaf`. A planned issue may use `"branch": null`. Local filesystem paths do not belong in the issue.

## Lifecycle

| GitHub state | Meaning |
| --- | --- |
| Open issue, no differing commit | Planned |
| Draft pull request | In progress |
| Ready pull request | In review |
| Open native blocker | Blocked |
| Merged pull request and closed issue | Complete |

Use a direct PR to `main` for one stream. For parallel work, bind the parent to a short-lived integration branch and create independently mergeable child issues whose leaf PRs target it. Closing keywords operate only when the PR targets the default branch; close merged leaf issues explicitly.

## Common operations

```powershell
gh issue view <number> --comments
gh issue edit <number> --add-assignee '@me'
gh issue edit <blocked> --add-blocked-by <blocker>
gh issue comment <number> --body-file <public-handoff-file>
gh pr view <number> --comments
```

Use body files for multiline content. Before cleanup, require a merged PR, closed issue, clean worktree, and proof that the branch has no commits absent from its intended base.
