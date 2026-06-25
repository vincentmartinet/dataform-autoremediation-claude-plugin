# Changelog

## [0.10.0] - 2026-06-25

### Added
- Implemented "live test" validation against BigQuery. After a successful `dataform compile`, the daemon creates a temporary dataset, replicates the direct dependencies (schemas), and runs `dataform run --dry-run` to ensure runtime queries (like missing columns or types) are valid.
- Added `live_test.py` leveraging the `bq` CLI and `dataform` CLI without requiring new Python dependencies.
- ADR-0014: Live Test Validation.

## [0.9.0] - 2026-06-25

### Changed
- Migrated plugin daemon lifecycle from a 1:1 session-bound process to a 1:N singleton architecture that persists across multiple Claude Code sessions.
- `SessionStart` hook now registers its Claude Session PPID into a `.lock` file in `/tmp/dataform-scout-sessions/`.
- `SessionEnd` hook no longer forcefully kills the python daemon. It now simply unregisters its lock file.
- The Python daemon now runs a background thread verifying active sessions using `os.kill(pid, 0)`, cleaning up stale lock files from crashed sessions, and exiting cleanly only when 0 sessions remain.
- ADR-0013: 1:N Plugin Lifecycle using Targeted Pidfile Liveness.

## [0.8.5] - 2026-06-25

### Added
- Added `workspace_base_dir` to the daemon configuration. When configured, the daemon will use `tempfile` to create isolated ephemeral subdirectories inside the configured base directory for the `git clone` workspace, rather than defaulting to the OS-managed `/tmp` directory. This allows the Git clones to correctly inherit Git configuration (like SSH keys, email, or GPG keys) that the user may have configured via `includeIf "gitdir:..."`.
- ADR-0012: Documented the decision to use a configurable workspace root for Git `includeIf` inheritance.

### Changed
- Shifted workspace garbage collection into the daemon lifecycle. By leveraging Python's `tempfile.TemporaryDirectory` context manager, the ephemeral clone directory is guaranteed to be deleted when the fix process finishes or crashes, rather than relying on OS-level `/tmp` directory garbage collection.

## [0.8.4] - 2026-06-25

### Added
- `plans/configuration_ideas.md` containing 10 ideas for new configurable properties based on currently hard-coded values.
- `docs/specifications.md` containing the high-level overview, triggers, error handling workflow, and current challenges of the plugin. Added explicit `Configuration` section.
- `SessionEnd` hook and `src/hooks/session-end.sh` script to automatically stop the daemon and free resources when a Claude Code session ends.
- ADR-0011: Stop Daemon on Session End.

## [0.8.3] - 2026-06-24

### Fixed
- Added a try-except block around `subprocess.Popen` when starting the `gcloud alpha logging tail` process to prevent the daemon from crashing if the process fails to spawn due to OS errors.
- Spawns a background thread to capture and log any error messages output to `stderr` by `gcloud alpha logging tail` if the command fails during runtime.
- Added a check in `src/hooks/session-start.sh` to verify if the `grpcio` package is installed and emits a `systemMessage` to alert the user if missing, ensuring `gcloud alpha logging tail` works out of the box.
- Configured the daemon to set `CLOUDSDK_PYTHON=sys.executable` and `CLOUDSDK_PYTHON_SITEPACKAGES=1` in the gcloud subprocess environment. This forces `gcloud alpha logging tail` to use the same Python interpreter as the daemon, ensuring it has access to the user's `grpcio` package required for live tailing without mismatch errors.
- Fixed a bug where `json.loads` would constantly fail on the `gcloud alpha logging tail --format=json` stream output because it prints a continuous comma-separated JSON array. The daemon now strips trailing commas and ignores array brackets, properly parsing each log entry.
- Fixed a bug where log entries were ignored by the daemon because `gcloud alpha logging tail` outputs `snake_case` keys (e.g. `json_payload`) while `gcloud logging read` outputs `camelCase` keys (e.g. `jsonPayload`). `models.py` now supports both formats.
- Fixed an issue where the real-time log watcher would ignore new errors after startup because of standard output buffering when piping `gcloud alpha logging tail`. Set `PYTHONUNBUFFERED=1` to force immediate line-by-line flushing.
- Fixed an issue where missing Python docstrings and long lines caused linting errors by adding docstrings, fixing line lengths, and configuring PyProject linting rules.

## [0.8.2] - 2026-06-24

### Added
- Log all Git configuration (email, gpgkey, etc.) whenever the daemon handles an error.
- Added explicit logging when failed actions are empty or when duplicate failures are skipped by the cache to improve observability in `src/scout_daemon.py`.
- Added a new `clear-cache` option to the `/scout-configure` command (and skill) that triggers a `SIGUSR1` signal to the daemon, allowing users to manually clear the in-memory deduplication cache without restarting the service.

## [0.8.1] - 2026-06-22

### Added
- Added an interactive macOS dialog that prompts the user for confirmation after a successful fix. If confirmed, the daemon autonomously pushes the fix branch and opens a Pull Request using `gh pr create`.
- ADR-0010: Documented the decision to use `gh repo clone` over `git clone` to avoid headless authentication failures.

### Fixed
- Fixed an issue where PR creation failed due to uncommitted files by ensuring `git commit` is executed before `git push` and `gh pr create`.
- Fixed an issue where `git push` failed with a headless authentication error during Pull Request creation by configuring `!gh auth git-credential` as the local credential helper immediately after cloning.
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
