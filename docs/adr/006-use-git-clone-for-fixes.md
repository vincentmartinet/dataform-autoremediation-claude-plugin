# ADR-0006: Use Git Clone for Fixes

## Status
Accepted

## Context
ADR-0005 introduced the use of `git worktree` to isolate Claude Code's automated fixes. However, this still required the user to have the specific Dataform repository cloned locally, and the plugin could only fix errors if it was started inside a matching local repository directory.

Since Dataform projects often consist of multiple repositories or environments, limiting the agent to the current local repository restricted its usefulness as a background daemon.

## Decision
1. **Deduce Remote URL:** The daemon now dynamically queries the Dataform API (`gcloud dataform repositories describe`) to extract the `gitRemoteSettings.url` for the failing repository.
2. **Fresh Clone:** Instead of using the user's local working tree or a `git worktree`, the daemon performs a fresh `git clone` of the repository into a temporary `/tmp/` directory.
3. **No Local Dependency:** The local repository matching constraint has been completely removed. The daemon can now autonomously resolve and fix errors for *any* repository in the GCP project.

## Consequences
- **Positive**:
  - The plugin operates completely autonomously and can fix errors across multiple repositories without requiring the user to have them all cloned locally.
  - Zero interference with the user's local git configuration or uncommitted work.
- **Negative**:
  - `git clone` requires network overhead for each fix, which might be slower than a local `git worktree` checkout.
  - The fix branch (`fix/dataform-...`) lives entirely in the `/tmp/` clone. Users will need to manually inspect or fetch the branch from `/tmp/` if they wish to merge it locally (assuming the agent doesn't autonomously push it, per the current boundary rules).
