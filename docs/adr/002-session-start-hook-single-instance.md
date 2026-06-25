# ADR-0002: SessionStart Hook with PID-File Single-Instance Guard

## Status
Accepted

## Context
The scout daemon should start automatically when a developer opens a Claude Code session in this project, without requiring them to run `/scout` manually. However, developers often have multiple Claude Code sessions open simultaneously, and starting a daemon per session would produce duplicate log consumers and redundant fix attempts.

## Decision
Register a `SessionStart` hook in `src/hooks/hooks.json` that executes `src/hooks/session-start.sh` on every session start. The shell script uses a PID file at `/tmp/dataform-scout.pid` as a mutex:
- If the file exists and the recorded PID is alive → exit silently (no-op).
- If the file is absent or the PID is stale → launch the daemon via `nohup`, write the new PID.

The daemon cleans up the PID file on graceful shutdown (SIGINT/SIGTERM).

## Consequences
- **Positive:** Zero-friction startup — developers get log monitoring without any manual step.
- **Positive:** Guaranteed single instance regardless of how many sessions are open.
- **Negative:** PID file in `/tmp` is not cleaned up on hard crashes (kernel kill, power loss). On the next session start the stale PID check (`kill -0`) will detect this and restart correctly, so it self-heals.
- **Negative:** `/tmp` is process-local to the machine; does not work in multi-machine or container setups (out of scope).
