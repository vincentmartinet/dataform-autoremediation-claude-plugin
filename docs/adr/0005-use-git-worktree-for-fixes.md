# ADR-0005: Use Git Worktree and Verify Target Repository For Fixes

## Status
Accepted

## Context
When an error log is detected by the daemon, it triggered `git checkout -b fix/dataform-...` directly in the current working directory. This caused multiple problems:
1. It branches off the current working branch, which may not be the branch where the error actually occurred.
2. It interrupts the user's ongoing work by switching branches underneath them.
3. Because the daemon runs in whatever directory the user started Claude in, it could apply fixes for a GCP project/repository error inside a completely unrelated local repository.

## Decision
1. **Repository Verification**: The daemon now inspects `workflow_settings.yaml` (or `dataform.json`) and runs `git remote -v` to verify that the local repository matches the `project_id` and `repository_id` present in the error log. If there is a mismatch, the error is skipped.
2. **Dynamic Branching**: For Workflow Invocations, the daemon attempts to fetch the exact `gitCommitish` (branch name) from the Dataform API. For Workspace errors, it uses the `workspace_id`.
3. **Git Worktree**: Instead of checking out the branch in the user's current directory, the daemon uses `git worktree add` to create an isolated directory (e.g. `/tmp/dataform-scout-...`) to run the Claude fix.

## Consequences
- **Positive**:
  - The user's active working directory is completely isolated from the AI fix.
  - The fix starts from the actual branch that failed, improving contextual correctness.
  - Fixes are not accidentally applied to the wrong local repositories.
- **Negative**:
  - Requires `git worktree` command support (standard in modern Git, but older setups might have issues).
  - `/tmp/` directory accumulation if worktrees are not cleaned up (though Git's automatic gc handles disconnected worktrees over time).
