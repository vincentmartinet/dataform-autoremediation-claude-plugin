# Configurable Workspace Root

## Context and Problem Statement

When the Scout Daemon clones a repository to fix a Dataform error, it historically cloned the repository into the OS-default temporary directory (`/tmp`). However, Git configurations (such as user email, GPG keys, or SSH credentials) are often scoped to specific directories using Git's `includeIf "gitdir:..."` directive. Because `/tmp` falls outside of these configured directory structures, the cloned repository failed to inherit the user's specific configurations (like their work email or company GPG key), leading to commits with incorrect authors or failed pushes. 

Additionally, because the `/tmp` directory relies on OS-level garbage collection, aborted or failed daemon processes could leave behind orphaned clones.

## Decision

We decided to introduce a `workspace_base_dir` configuration setting and shift the directory lifecycle management into Python using `tempfile.TemporaryDirectory`.

If the user sets `workspace_base_dir` (e.g., `~/work/company/.scout-workspaces/`), the daemon will instruct Python's `tempfile` module to create its ephemeral subfolders inside that root directory.

## Consequences

- **Good:** Cloned repositories now correctly inherit Git configurations configured via `includeIf`.
- **Good:** Because we use `tempfile.TemporaryDirectory` as a context manager around the Git clone and fix execution, the temporary folder is guaranteed to be deleted when the fix process finishes, succeeds, or crashes—preventing disk bloat.
- **Good:** Concurrency is preserved, as `tempfile` ensures a collision-free subfolder is generated for each run.
- **Bad:** Users who need this feature must manually define the `workspace_base_dir` in their configuration file.
