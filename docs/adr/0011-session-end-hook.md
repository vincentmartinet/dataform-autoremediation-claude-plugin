# ADR-0011: Stop Daemon on Session End

## Status
Accepted

## Context
The plugin starts the `scout_daemon.py` on `SessionStart` and tracks its single instance using a PID file (`/tmp/dataform-scout.pid`). Currently, the daemon continues running in the background indefinitely even after the user exits Claude Code. We want to stop the plugin automatically when the session ends to free up resources.

## Decision
Register a `SessionEnd` hook in `hooks/hooks.json` that executes `src/hooks/session-end.sh` when a Claude Code session terminates. The script will read the PID from `/tmp/dataform-scout.pid`, gracefully kill the daemon, and remove the PID file.

## Consequences
- **Positive:** No lingering background processes consuming system resources after Claude Code is closed.
- **Positive:** Cleaner lifecycle management matching the plugin's usage.
- **Negative:** If a user has multiple Claude Code sessions open concurrently, closing *one* of them will trigger `SessionEnd` and kill the daemon for *all* of them. The daemon will not restart until a new session is opened. Given the use case, this trade-off is acceptable over implementing complex IPC reference counting.
