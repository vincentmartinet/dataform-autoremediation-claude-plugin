# dataform-scout

A Claude Code plugin that monitors Google Cloud Dataform error logs. When an error is caught, it automatically clones the affected repository into a temporary directory, creates a fix branch, and instructs headless Claude Code to fix the failing `.sqlx` file — all using your active local credentials.

## Prerequisites

| Tool | Verify |
|------|--------|
| `gcloud` CLI | `gcloud --version` |
| `gcloud alpha` component | `gcloud components list \| grep alpha` |
| `dataform` CLI | `dataform --version` |
| `claude` CLI | `claude --version` |
| `git` CLI | `git --version` |
| `uv` | `uv --version` (for development) |
| Active gcloud auth | `gcloud auth list` (at least one `*` account) |
| Correct project set | `gcloud config list project` |

Install missing components:
```sh
gcloud components install alpha
npm install -g @dataform/cli
```

## Installation

Clone this repository, then load it as a local plugin:

```sh
claude --plugin-dir /path/to/dataform-scout
```

Once published to a marketplace:
```
/plugin install owner/dataform-scout
```

## First-time setup

Before the daemon can watch logs, configure which GCP resource to monitor:

```
/dataform-scout:scout-configure
```

This will ask for a project ID, folder ID, or organization ID and write the config to `~/.config/dataform-scout/config`.

## Usage

The scout daemon starts **automatically** when Claude Code launches (via the `SessionStart` hook), as long as a config exists. No manual command needed.

For each error detected, the plugin will:
- Deduplicate identical errors within a 5-minute rolling window.
- Fetch the Git remote URL and failing workspace branch directly from the Dataform API.
- Clone the repository to `/tmp/dataform-scout-<timestamp>` and create a new branch `fix/dataform-<timestamp>`.
- Invoke the `fix-dataform` skill headlessly to read, patch, and verify the failing `.sqlx` file.
- Attempt to fix the compilation error up to 3 times (anti-loop circuit breaker).
- Notify you natively via macOS notifications when an error is caught and when a fix succeeds or fails.

The plugin operates fully isolated in `/tmp` and **never** pushes to any remote.

## Verifying authentication

```sh
# Check active Google Cloud accounts
gcloud auth list

# Check active project
gcloud config list project

# Test log access manually
gcloud logging read 'resource.type="dataform.googleapis.com/Repository" AND severity>=ERROR' \
  --format=json --limit=5
```

## Troubleshooting

- **`gcloud alpha logging tail` not found** — install the alpha component: `gcloud components install alpha`.
- **No logs returned** — confirm your active project has Dataform repositories and that Cloud Logging is enabled.
- **`claude` or `git` not found** — ensure both the Claude Code CLI and Git CLI are installed and on your `PATH`.

## Development

This project uses `uv` for dependency management and testing.
```sh
# Setup environment and install dev dependencies
uv sync

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
uv run pylint src/ tests/

# Type checking
uv run mypy src/ tests/

# Run tests
uv run pytest --cov=src
```
