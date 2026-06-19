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
