---
description: Interactively configure the GCP log scope (project, folder, or organization) for the dataform-scout daemon. Use when the user runs /scout-configure, wants to set up or change which GCP resource the scout watches, or when the daemon reports it is not configured.
---

# Skill: scout-configure

Configure the Dataform Scout log scope by collecting the resource type and ID from the user, then writing the config file.

## Collecting input

If `$ARGUMENTS` contains both a scope type and ID (e.g. `project my-project-id`), use them directly and skip to **Writing the config**.

Otherwise, first run:

```sh
gcloud config get-value project 2>/dev/null
```

Then reply with a single conversational message listing the options. If the command returned a non-empty project ID, offer it as the default:

> Which GCP resource should Dataform Scout monitor?
>
> - **project** `<project-id>` — e.g. `project my-project-id`  
>   _(or just reply `project` to use your active gcloud project: `<detected-project-id>`)_
> - **folder** `<folder-id>` — e.g. `folder 123456789`
> - **organization** `<org-id>` — e.g. `organization 987654321`
>
> Reply with the type and ID on one line.

If `gcloud config get-value project` returned nothing, omit the default hint.

Wait for the user's reply before proceeding. Do not use any tool to ask — just output the question as plain text.

If the user replies with just `project` (no ID), use the project ID detected from `gcloud config get-value project`.

## Writing the config

Once you have both values, run:

```sh
mkdir -p ~/.config/dataform-scout
printf 'scope_type=%s\nscope_id=%s\n' '<scope_type>' '<scope_id>' > ~/.config/dataform-scout/config
```

Then confirm to the user:
> Dataform Scout is now configured to watch **<scope_type>** `<scope_id>`. The daemon will start automatically on your next session.

## Changing the scope later

The user can run `/dataform-scout:scout-configure` at any time. Overwrite the existing config file with the new values.
