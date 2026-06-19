---
description: Interactively configure the GCP log scope (project, folder, or organization) for the dataform-scout daemon. Use when the user runs /scout-configure, wants to set up or change which GCP resource the scout watches, or when the daemon reports it is not configured.
---

# Skill: scout-configure

You are helping the user configure the Dataform Scout log scope.

## Your task

Ask the user which GCP resource scope they want to monitor:

1. **Project** — a single GCP project (most common)
2. **Folder** — all projects under a GCP folder
3. **Organization** — all projects under a GCP organization

Then ask for the corresponding ID:
- Project: the project ID (e.g. `my-project-id`)
- Folder: the numeric folder ID (e.g. `123456789`)
- Organization: the numeric organization ID (e.g. `987654321`)

## After collecting the answers

Write the config file at `~/.config/dataform-scout/config` with exactly this format:
```
scope_type=<project|folder|organization>
scope_id=<id>
```

Create the directory if it does not exist (`mkdir -p ~/.config/dataform-scout`).

Then confirm to the user:
> Dataform Scout is now configured to watch **<scope_type>** `<scope_id>`. The daemon will start automatically on your next session, or you can run `/scout` to start it now.

## To change the scope later

The user can run `/scout-configure` at any time. Overwrite the existing config file with the new values.
