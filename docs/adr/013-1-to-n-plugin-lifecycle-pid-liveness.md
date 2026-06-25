# ADR-0013: 1:N Plugin Lifecycle using Targeted Pidfile Liveness

## Status
Accepted

## Context
The Dataform Scout plugin requires a background Python daemon to continuously poll Google Cloud logs. 
Initially, the daemon was tightly coupled to a single Claude Code session (1:1 architecture) via `SessionStart` and `SessionEnd` hooks. 
This approach had several flaws:
1. **Zombies on Crash**: If the user forcefully closed the terminal, `SessionEnd` would never fire, leaving the daemon orphaned and running forever.
2. **Concurrency Conflicts**: If a user opened two terminals in the same workspace, closing the first terminal would trigger `SessionEnd` and kill the daemon that the second terminal was still relying on.
3. **Hook Limitations**: The Claude Code hook system relies on synchronous bash scripts, making it impossible to hold long-lived IPC connections (like Unix Domain Sockets) open from the client side without blocking the UI.

## Decision
We decided to migrate to a shared singleton backend (1:N architecture) using a targeted Pidfile Liveness check mechanism.

1. **Session Start**: The `SessionStart` hook extracts the Claude Code parent process ID (`$PPID`) and creates a lock file in a shared directory (`/tmp/dataform-scout-sessions/<PID>.lock`). It then boots the daemon detached via `nohup` (if not already running).
2. **Session End**: The `SessionEnd` hook simply deletes its specific lock file. It does *not* kill the daemon.
3. **Liveness Verification (The Daemon)**: The Python daemon runs an internal background thread that wakes up every 30 seconds. It sweeps the `/tmp/dataform-scout-sessions/` directory, extracts the PIDs, and uses `os.kill(pid, 0)` to verify if the OS process is still alive. 
    * If `os.kill` throws an `OSError`, the session crashed, and the daemon deletes the stale lock file.
    * If zero active sessions are found, the daemon gracefully shuts itself down.

## Consequences
### Positive
* **Crash Resilience**: The daemon automatically cleans up after crashed or force-killed sessions without relying on `SessionEnd`.
* **Multi-Terminal Support**: Multiple Claude Code sessions can now share a single polling daemon smoothly.
* **Simplicity**: `os.kill(pid, 0)` is a native, zero-cost POSIX system call. We avoided complex IPC, external dependencies like `psutil`, and dirty OS process scraping.

### Negative
* **PID Wrap-Around Risk**: In astronomically rare cases (e.g., a machine left running for many months), the OS might recycle the exact PID of a crashed Claude session for an unrelated process, causing the daemon to stay alive indefinitely. This is an acceptable risk for a local developer tool.
