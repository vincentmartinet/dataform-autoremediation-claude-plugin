# ADR-0010: Use GitHub CLI (gh) for Cloning Repositories

## Status
Accepted

## Context
The Dataform Scout Daemon runs as a background process and automatically checks out the user's remote repositories to apply AI-generated fixes using Claude Code. During initial implementation and subsequent refactors, we encountered critical authentication failures when attempting to clone private GitHub repositories via `git clone` without interactive prompts (`fatal: could not read Username for 'https://github.com': Device not configured`). Because standard Git is often not configured with credentials suitable for a background headless daemon, the cloning step failed silently.

## Decision
We decided to use `gh repo clone` instead of the standard `git clone` for all remote repository cloning operations in `GitOpsService`. The GitHub CLI (`gh`) seamlessly leverages its authenticated state and handles required tokens internally, ensuring that unattended clones of private repositories succeed.

Additionally, to prevent regressions where developers might accidentally revert to `git clone` (as happened in v0.6.0), explicit inline documentation has been added to the cloning function, and `gh` has been added to the daemon's required startup dependencies check.

## Consequences

**Positive:**
- Fixes headless authentication errors when cloning private GitHub repositories.
- Zero extra configuration needed for developers already logged in via `gh auth login`.

**Negative:**
- Introduces `gh` as a hard dependency to run the Scout Daemon.
- If users are not authenticated in `gh` or do not use GitHub as their remote Git provider, cloning will fail. (A future ADR could address generic Git credential helpers for non-GitHub environments, but for this project's scope, GitHub CLI is standard).
