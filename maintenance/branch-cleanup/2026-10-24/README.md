# Remote branch cleanup — 2026-10-24

Scope: remove 22 redundant remote branch names, not commits, models or LFS objects.

## Evidence and safeguards

- `recovery-manifest.json`: exact branch → SHA → merged PR mapping, ancestry and tree checks.
- All eligible heads are ancestors of retained `main`; GitHub PR head refs also matched.
- Recovery evidence landed on `main` in PR #23 before execution.
- One-shot workflow checks current default branch, protection, open PRs, merged PR head and ancestry.
- Atomic push uses an explicit expected-SHA lease per branch; a moved head aborts the batch.
- Local synthetic Git test confirmed that moving 1 of 2 branches preserves both during atomic deletion.
- No repository settings, local worktrees, LFS objects or commit history are removed.
- At this cleanup stage, 21 unmerged pilot/feasibility branches and active glands
  branches were excluded. The later [completed-branch archive](../../archive/completed-branches/2026-10-24/README.md)
  preserves the subsequently retired pilot heads; this is not a current branch inventory.

## Restore a removed branch

Use the exact `expected_sha` and branch name from the manifest:

```sh
git fetch origin main
git branch '<branch-name>' '<expected_sha>'
git push origin 'refs/heads/<branch-name>:refs/heads/<branch-name>'
```

If needed, the corresponding `refs/pull/<number>/head` is another source for the original head. Verify its SHA against the manifest before restoring. Restoration does not require downloading LFS payloads.

## Receipt

See `execution-receipt.json` and the linked Actions run for the actual deletion list, skipped branches and postflight inventory. Branch counts can change afterward as active work proceeds.
