# Future Configuration Ideas

Here is a prioritized list of 10 configuration ideas based on hard-coded values currently in the codebase, ordered from most impactful/useful to nice-to-have quality-of-life tweaks:

### 1. Pull Request Automation Mode (`AUTO_PR_MODE`)
- **Currently:** Hard-coded to always pop up a macOS dialog asking for confirmation (`ask_confirmation` in `notifications.py`).
- **Why it's useful:** Constant dialog boxes interrupt flow. Users will want options like `always_ask` (default), `auto_pr` (fully autonomous without interruption), or `never_pr` (just fix locally and leave the branch).

### 2. Maximum LLM Fix Attempts (`MAX_FIX_ATTEMPTS`)
- **Currently:** Hard-coded to `3` in `constants.py`.
- **Why it's useful:** Gives users direct control over LLM token costs vs. problem-solving persistence. A "fail-fast" user might set it to `1`, while someone relying heavily on the agent overnight might set it to `5`.

### 3. Claude Invocation Timeout (`CLAUDE_TIMEOUT_SECONDS`)
- **Currently:** Hard-coded to `120` seconds in `claude_invoker.py`.
- **Why it's useful:** Large Dataform repositories or complex `.sqlx` files take longer for Claude to read and patch. Users with large codebases will quickly hit the 120s ceiling and need to increase this to `300` or more.

### 4. Deduplication Cache Window (`DEDUPLICATION_WINDOW_SECONDS`)
- **Currently:** Hard-coded to `300` seconds (5 minutes) in `scout_daemon.py`.
- **Why it's useful:** In noisy environments or for pipelines that automatically retry, 5 minutes might be too short, leading to the agent spawning multiple fix branches for the exact same issue.

### 5. Protected / Ignored Branches (`IGNORE_BRANCHES`)
- **Currently:** No branch restrictions; it attempts to fix whatever branch the API says failed.
- **Why it's useful:** A critical safety feature. Users likely want to specify `IGNORE_BRANCHES=["main", "master", "prod"]` so the agent only attempts automated fixes on dev or feature branches.

### 6. Startup Lookback Window (`LOOKBACK_HOURS`)
- **Currently:** Hard-coded to `24` hours in `scout_daemon.py`.
- **Why it's useful:** If a user only wants real-time fixes, they might set this to `0` to avoid being flooded with PRs from overnight failures the moment they open Claude Code. Conversely, after a long weekend, they might want to bump it to `72`.

### 7. Actionable Error Categories (`ACTIONABLE_CATEGORIES`)
- **Currently:** Hard-coded to only proceed if the category is `FIXABLE_LLM` (ignoring `DATA`, `INFRA`, `UNKNOWN`).
- **Why it's useful:** Power users might want to experiment with letting Claude try to fix `UNKNOWN` or `DATA` errors, rather than restricting it strictly to syntax/compilation issues.

### 8. Temporary Workspace Directory (`WORKSPACE_DIR`)
- **Currently:** Hard-coded to `/tmp/dataform-scout-<timestamp>` in `git_ops.py`.
- **Why it's useful:** Some corporate laptops restrict executing shell scripts or git hooks from `/tmp`. Allowing users to set this to `~/.dataform-scout/workspaces` provides better compatibility and easier manual inspection of failed runs.

### 9. Minimum Log Severity (`MIN_LOG_SEVERITY`)
- **Currently:** Hard-coded to `severity>=ERROR` in the `LOG_FILTER`.
- **Why it's useful:** Some Dataform setups are configured to emit `WARNING` logs that actually indicate structural issues. Letting users lower the threshold allows the agent to be more proactive.

### 10. Notification Toggles & Sounds (`DISABLE_NOTIFICATIONS` / `NOTIFICATION_SOUND`)
- **Currently:** Always sends macOS alerts using the "Basso" sound.
- **Why it's useful:** A pure quality-of-life setting. Users running the agent purely in the background might want to silence the native macOS popups or change the alert sound to something less intrusive.
