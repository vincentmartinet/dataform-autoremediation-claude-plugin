# dataform-scout

A Claude Code plugin that monitors Google Cloud Dataform error logs, automatically branches your local git repository when an error is caught, and instructs Claude Code to fix the failing `.sqlx` file — all using your active local credentials.

## Prerequisites

| Tool | Verify |
|------|--------|
| `gcloud` CLI | `gcloud --version` |
| `gcloud alpha` component | `gcloud components list \| grep alpha` |
| `dataform` CLI | `dataform --version` |
| `claude` CLI | `claude --version` |
| Active gcloud auth | `gcloud auth list` (at least one `*` account) |
| Correct project set | `gcloud config list project` |

Install missing components:
```sh
gcloud components install alpha
npm install -g @dataform/cli
```

## Installation

```
/plugin install path/to/dataform-scout
```

Or, if published to the Claude Code Marketplace:
```
/plugin install dataform-scout
```

## Usage

Open Claude Code inside your Dataform repository root, then run:

```
/scout
```

This will:
1. Perform a **24-hour lookback** — fetching all `severity=ERROR` logs from your Dataform repositories.
2. Start a **real-time stream** — tailing new errors as they arrive.

For each error detected, the plugin will:
- Create a local branch `fix/dataform-<timestamp>`.
- Invoke the `fix-dataform` skill to read, patch, and verify the failing `.sqlx` file.
- Show you the diff and ask for confirmation before leaving the branch in place.

The plugin **never** pushes to any remote.

## Verifying gcloud authentication

```sh
# Check active accounts
gcloud auth list

# Check active project
gcloud config list project

# Test log access manually
gcloud logging read 'resource.type="dataform.googleapis.com/Repository" AND severity=ERROR' \
  --format=json --limit=5
```

## Troubleshooting

- **`gcloud alpha logging tail` not found** — install the alpha component: `gcloud components install alpha`.
- **No logs returned** — confirm your active project has Dataform repositories and that Cloud Logging is enabled.
- **`claude` not found** — ensure Claude Code CLI is installed and on your `PATH`.
