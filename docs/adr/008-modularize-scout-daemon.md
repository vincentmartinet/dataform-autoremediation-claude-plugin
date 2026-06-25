# ADR-0008: Modularize Scout Daemon

## Status
Accepted

## Context
The `src/scout_daemon.py` file had grown to nearly 600 lines. It combined multiple responsibilities into a single file:
- Dataform and GCP error parsing
- Google Cloud API interaction (fetching repo URLs and workflow configs)
- Git repository operations (cloning and checking out)
- Claude Code invocation (`claude` CLI)
- Native macOS notifications
- Core daemon event loop (polling and streaming logs)

This monolithic design made it difficult to maintain, test, and read, violating the Single Responsibility Principle.

## Decision
We decided to split `src/scout_daemon.py` into multiple distinct Python modules within the `src/` directory.

The new file structure separates responsibilities:
- `src/models.py`: Dataclass models (`LogEntry`).
- `src/error_classification.py`: Constants and logic for categorizing errors (LLM fixable vs Infrastructure vs Data).
- `src/gcp_api.py`: Wrappers around `gcloud` subprocess calls and REST APIs.
- `src/git_ops.py`: Local Git and GitHub CLI operations.
- `src/claude_invoker.py`: Logic for running the `claude` subprocess with the appropriate skills.
- `src/notifications.py`: macOS native `osascript` notifications.
- `src/constants.py`: Common configuration variables and constants.
- `src/scout_daemon.py`: The entrypoint and orchestrator, importing and using the separated modules.

We kept all files in the same directory (`src/`) to ensure simple local imports continue to work without needing to structure it as a full installable Python package, maintaining simplicity.

## Consequences
**Positive:**
- Improved readability: Each module handles a single specific concern.
- Easier testing: Isolated functions can be unit-tested without loading the entire daemon.
- Maintainability: Finding and fixing bugs is more localized.

**Negative:**
- Requires slightly more effort to manage imports between files.
