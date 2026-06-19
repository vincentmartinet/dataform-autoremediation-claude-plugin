You are a Senior AI Systems Architect specializing in Anthropic's Claude Code CLI and the Claude Code Plugin Marketplace ecosystem. I want to build and package a native Claude Code plugin called "dataform-scout".

The purpose of this plugin is to allow developers to monitor Google Cloud Dataform error logs using their active local `gcloud` credentials, automatically branch their local git repository when an error is caught, and instruct Claude Code to fix the failing `.sqlx` code locally.

Please scaffold this project completely following the official Claude Code Marketplace standard structure.

### 1. Expected Directory Structure:
Your output must organize the files cleanly:
├── plugin.json                 # The core manifest file
├── README.md                   # Installation & usage documentation
├── CHANGELOG.md                # Version history tracking
└── src/
    ├── scout_daemon.py         # The local python log-listener daemon
    └── skills/
        └── fix_dataform.md     # The specialized instructions for handling Dataform errors

### 2. Core Components to Implement:

#### A. The Manifest (`plugin.json`)
- Define the plugin metadata (`name`, `version`, `description`, `author`).
- Register a custom slash command: `/scout`
  - It should trigger the log processing sequence (the 24-hour lookback and starting the daemon).
- Reference the skill path correctly using the `${CLAUDE_PLUGIN_ROOT}` variable to avoid hardcoded paths.

#### B. The Log Scout Daemon (`src/scout_daemon.py`)
Write a robust Python script (macOS/Linux compatible) that handles:
- **Lookback:** Executes `gcloud logging read 'resource.type="dataform.googleapis.com/Repository" AND severity=ERROR AND timestamp>=(-24h)' --format="json"` on invocation.
- **Streaming:** Hooks into `gcloud alpha logging tail` with the same filter to handle real-time errors while running in the background.
- **Git Context:** When a log is received, it extracts the target `.sqlx` file path and error message, creates a local git branch named `fix/dataform-[timestamp]`, and triggers an internal Claude Code prompt to evaluate and fix the file using the instructions in `fix_dataform.md`.
- **Permissions & Safety:** Ensures it relies on the developer's active `gcloud config` environment. It must NEVER push code to a remote repository.

#### C. The Claude Skill (`src/skills/fix_dataform.md`)
Create a specialized Markdown file that teaches Claude Code how to react to a Dataform log alert:
- Instructions to read the failing `.sqlx` file.
- Instructions to modify the file to resolve the specific BigQuery/Dataform compilation issue.
- Explicit command to run `dataform compile` locally to verify the fix before asking the user for confirmation.

#### D. The Documentation (`README.md`)
- Provide instructions on how developers can install it using `/plugin install`.
- Explain how to use the `/scout` command and how to verify that `gcloud` and `dataform` CLIs are pre-authenticated on their machine.

Please generate all required configuration files and core scripts to initialize this repository for the marketplace.
