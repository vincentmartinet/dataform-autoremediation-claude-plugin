# ADR-0001: Plugin Architecture — Python Daemon + Claude Code Skill

## Status
Accepted

## Context
We need a way to monitor GCP Dataform error logs continuously and trigger automated fixes without manual intervention. The fix logic requires LLM reasoning (reading `.sqlx` files, understanding BigQuery compilation errors), so it must delegate to Claude Code rather than being implemented as plain Python.

## Decision
Use a two-component architecture:
1. **`scout_daemon.py`** — a lightweight Python process responsible for log polling (24-hour lookback) and real-time streaming via `gcloud alpha logging tail`. It handles all git branching and subprocess orchestration.
2. **`fix_dataform.md`** — a Claude Code skill (Markdown instruction file) that encapsulates the LLM reasoning for diagnosing and patching `.sqlx` files.

The daemon invokes Claude Code headlessly (`claude -p <prompt>`) and passes context (file path, error message, branch name) at runtime.

## Consequences
- **Positive:** Clear separation between infrastructure concerns (daemon) and reasoning concerns (skill). Skills can be updated independently without touching the daemon.
- **Positive:** No LLM API key management needed — piggybacks on the user's active Claude Code session.
- **Negative:** Requires `claude` CLI to be in `PATH`; daemon degrades gracefully (writes prompt to temp file) if absent.
- **Negative:** Headless Claude Code invocations are not easily unit-testable.
