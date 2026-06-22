# Changelog

## [0.8.1] - 2026-06-22

### Added
- ADR-0010: Documented the decision to use `gh repo clone` over `git clone` to avoid headless authentication failures.

### Fixed
- Reinstated the use of `gh repo clone` instead of `git clone` in `src/git_ops.py` to seamlessly handle authentication for private GitHub repositories, which was accidentally reverted during the module refactoring.
- Re-added the dependency check for `gh` in `src/scout_daemon.py`.

## [0.8.0] - 2026-06-22

### Added
- Configured Ruff to enforce `pydocstyle` (`D` rules) with the Google convention for strict docstring requirements.
- Added missing docstrings and fixed docstring formatting across the `src/` directory to comply with the new rules.

### Changed
- `src/scout_daemon.py` & services - Refactored the core application into an Object-Oriented/Inversion of Control (IoC) architecture using Dependency Injection for all services (`GCPApiClient`, `GitOpsService`, `ErrorClassifier`, `ClaudeInvokerService`, `NotificationService`).
- Updated `tests/` to use manual injection of mocked classes instead of `unittest.mock.patch`.
- ADR-0009: Migrating to Object-Oriented Service Architecture with Dependency Injection.

## [0.7.0] - 2026-06-22

### Added
- Comprehensive test suite covering core modules (`tests/test_models.py`, `tests/test_error_classification.py`, `tests/test_gcp_api.py`, `tests/test_git_ops.py`, `tests/test_scout_daemon.py`) using `pytest` and `unittest.mock`.

### Fixed
- Tests no longer send actual macOS system notifications during execution (mocked `notify` in `test_scout_daemon.py`).
- Static typing checks using `mypy` and configured strict typing rules.
- Pre-commit configuration (`.pre-commit-config.yaml`) containing `ruff` (formatting and linting), `mypy`, `pylint`, and `pytest` to prevent malformed code submissions.

## [0.6.0] - 2026-06-22

### Changed
- `src/scout_daemon.py` — Refactored the monolithic daemon into multiple modular files (`models.py`, `error_classification.py`, `gcp_api.py`, `git_ops.py`, `claude_invoker.py`, `notifications.py`, `constants.py`) to improve readability, maintainability, and testing.
- ADR-0008: Documented the decision to modularize the Scout Daemon.

## [0.5.3] - 2026-06-22

### Added
- `src/scout_daemon.py` — implemented an in-memory deduplication cache (`_recent_failures`) with a 5-minute rolling window to prevent duplicate agent runs for identical errors.
- `src/scout_daemon.py` — added `MAX_FIX_ATTEMPTS = 3` anti-loop circuit breaker. The agent now attempts to fix an issue up to 3 times, validating with `dataform compile`, and gracefully reverts via `git checkout .` on failure.

### Changed
- `src/scout_daemon.py` — refactored log entry parsing to use built-in Python `dataclasses` (`LogEntry`) for strict schema validation, removing loose dictionary `.get()` lookups while maintaining a zero-dependency architecture.

### Fixed
- `src/scout_daemon.py` — added `git status --porcelain` check before checking out fix branches to prevent overriding dirty working trees.
- `src/scout_daemon.py` — added a global `try/except Exception` block in `_handle_entry` to ensure unexpected changes to the GCP log schema do not crash the daemon's real-time stream.

---

## [0.5.2] - 2026-06-22

### Changed
- `src/scout_daemon.py` — uses the `gh repo clone` command instead of `git clone` to seamlessly handle authentication for GitHub repositories.
- `src/scout_daemon.py` — added a startup dependency check for `gcloud`, `git`, `dataform`, and `gh` executables before running the main loop.

### Fixed
- `src/scout_daemon.py` — resolved macOS `/tmp` symlink issue by using `os.path.realpath` for the clone path, which prevents Claude Code from rejecting file edits due to strict workspace boundary checks.
- `src/scout_daemon.py` — added `--permission-mode auto` to the headless Claude invocation to ensure the agent doesn't block on tool permissions while editing `.sqlx` files or running shell commands in the temporary fix workspace.

---

## [0.5.1] - 2026-06-22

### Fixed
- `_get_gcp_repo_url` now uses the Dataform REST API via `urllib` instead of the `gcloud dataform` CLI component, which may not be installed or available by default, preventing silent failures when deducing the Git remote URL.

---

## [0.5.0] - 2026-06-22

### Added
- `src/scout_daemon.py` — intercepts `WorkflowInvocationCompletionLogEntry` errors that lack specific context and automatically queries the Dataform REST API (`/workflowInvocations/...:query`) to extract the exact BigQuery execution failures and target actions, enabling Claude to fix them.
- ADR-0004: Fetch Dataform Workflow Invocation Actions for Missing Context.

### Changed
- `src/scout_daemon.py` — uses `git clone` instead of `git worktree`/`git checkout` to apply automated fixes. The daemon now queries the Dataform API for the remote URL and clones it into a temporary `/tmp` directory, fully isolating Claude's work from any of the user's local repositories.
- `src/scout_daemon.py` — removes the local repository matching constraint; the daemon can now autonomously fix errors across any Dataform repository in the Google Cloud project without needing a local clone.
- `src/scout_daemon.py` — extracts the failing branch (`gitCommitish`) from the Dataform API or workspace instead of blindly branching from the current local branch.

### Fixed
- `SKILL_PATH` in `src/scout_daemon.py` pointed to non-existent `src/skills/fix_dataform.md`; corrected to `skills/fix-dataform/SKILL.md` where the skill actually lives.
- `_trigger_claude_fix` no longer passes the skill path as a string in the user prompt (causing "Permission denied for skill file" from Claude Code). Now reads the skill file content and passes it as `--system-prompt` to the headless `claude` invocation.
- Removed the unused `tempfile` import left over from the previous broken implementation.

## [0.4.0] - 2026-06-19

### Added
- `_notify()` in `src/scout_daemon.py` — fires a macOS system notification bubble (via `/usr/bin/osascript`) when an error log is detected, showing the affected `.sqlx` file and a "Creating fix branch…" subtitle. Notification fires before the git branch step so the user is alerted even if git fails.

---

## [0.3.0] - 2026-06-19

### Added
- `/scout-configure` command and `scout-configure` skill — interactive wizard to set the GCP log scope (project, folder, or organization) stored at `~/.config/dataform-scout/config`.
- `SessionStart` hook now injects a `systemMessage` on first run (no config file) prompting the user to run `/scout-configure` before the daemon starts.
- ADR-0003: log scope configuration decision.

### Changed
- `src/scout_daemon.py` — reads `~/.config/dataform-scout/config` at startup and appends the appropriate `--project` / `--folder` / `--organization` flag to all `gcloud` calls. Falls back to the active gcloud project if config is absent.
- `src/hooks/session-start.sh` — validates config presence and scope_type before starting daemon; emits actionable `systemMessage` on misconfiguration.
- `plugin.json` — bumped to `0.3.0`, registered `scout-configure` skill and command.

---

## [0.2.0] - 2026-06-19

### Added
- `SessionStart` hook (`src/hooks/hooks.json` + `src/hooks/session-start.sh`) — auto-starts the scout daemon on session open with a PID-file single-instance guard.
- ADR directory (`docs/adr/`) with MADR template and two initial records:
  - ADR-0001: Plugin architecture (Python daemon + Claude Code skill)
  - ADR-0002: SessionStart hook with single-instance guard

### Changed
- `src/scout_daemon.py` — daemon now removes `/tmp/dataform-scout.pid` on graceful shutdown.
- `plugin.json` — registered `hooks` field pointing to `src/hooks/hooks.json`.
- `CLAUDE.md` — added workflow rule to commit after every completed task.

---

## [0.1.0] - 2026-06-19

### Added
- Initial plugin scaffold (`plugin.json`, `README.md`, `CHANGELOG.md`).
- `src/scout_daemon.py` — 24-hour lookback + real-time `gcloud alpha logging tail` stream for Dataform errors.
- `src/skills/fix_dataform.md` — Claude Code skill for analysing and patching failing `.sqlx` files.
- `/scout` slash command registered in the plugin manifest.
