# ADR-0003: User-Configurable GCP Log Scope via /scout-configure

## Status
Accepted

## Context
The scout daemon previously fell back to the active `gcloud` project for all log queries. Developers working across multiple GCP projects, folders, or organizations needed a way to specify which resource scope to watch without touching environment variables or daemon internals.

The solution must be user-friendly inside Claude Code — not a raw env var or CLI flag.

## Decision
Introduce a `/scout-configure` command backed by a `scout-configure` skill. On first session start (when `~/.config/dataform-scout/config` is absent), the `SessionStart` hook injects a `systemMessage` prompting the user to run `/scout-configure`. The skill guides the user through choosing a scope type (project / folder / organization) and entering the corresponding ID, then writes:

```
~/.config/dataform-scout/config
scope_type=<project|folder|organization>
scope_id=<id>
```

The daemon reads this file at startup via `_load_scope_flags()` and appends `--project`, `--folder`, or `--organization` to both `gcloud logging read` and `gcloud alpha logging tail` invocations. If the file is absent, the daemon falls back to the active gcloud project (existing behavior).

The user can re-run `/scout-configure` at any time to overwrite the config.

## Consequences
- **Positive:** Zero friction for new users — they are guided on first session open.
- **Positive:** Config is user-scoped (`~/.config/`) so it persists across sessions and projects.
- **Positive:** Changing scope does not require editing code or env vars.
- **Negative:** Config change takes effect on the next daemon start (existing running daemon is not hot-reloaded). User must kill and restart, or wait for the next session.
- **Negative:** Config file is plain text with no validation at write time; daemon silently falls back to default if the file is malformed.
