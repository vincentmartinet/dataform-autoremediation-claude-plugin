# Dataform Scout — Project Configuration & Guardrails

## Project Overview
This project is a native Claude Code Marketplace plugin (`dataform-scout`) that monitors Google Cloud Dataform error logs using local `gcloud` credentials. When an error is caught, it checks out a local git branch and uses headless Claude Code to automatically attempt a code fix.

### Core Tech Stack
- Python 3.11+ (Log monitoring daemon)
- Pydantic (Log schema validation)
- Claude Code Plugin Framework (`plugin.json` + Agent Skills)
- Google Cloud SDK (`gcloud` CLI)

---

## Workspace Layout
- `plugin.json` - Plugin manifest and slash command definition (`/scout`)
- `src/scout_daemon.py` - Background log listener python script
- `src/skills/fix_dataform.md` - Specialized agent instructions for Dataform fixes

---

## Critical Safety & Execution Rules
You must strictly follow these constraints when writing, modifying, or testing code in this repository:

### 1. Python Stability & Defensive Coding
- Use **Pydantic** models (`BaseModel`) to strictly validate incoming GCP log JSON. Never use loose dictionary lookups.
- Wrap log parsing in `try/except` blocks to prevent the daemon from crashing if GCP updates its schema.
- Before running the main loop, check the user's `PATH` for `gcloud`, `git`, and `dataform`. Gracefully exit with an error message if any are missing.

### 2. Circuit Breakers (Anti-Loop Protection)
- Limit headless fix attempts to a maximum of 3 (`MAX_FIX_ATTEMPTS = 3`).
- If `dataform compile` still fails after 3 attempts, run `git checkout .` to revert the AI's edits, delete the temporary branch, and notify the user.
- Enforce a strict 120-second timeout on all headless execution subprocesses.

### 3. Git Protection
- Run `git status --porcelain` before checking out a branch. Abort if the working directory is dirty.
- **Strict Prohibition:** Never write or execute commands that perform `git push`, `git merge`, or any remote-destructive operations. The agent boundary ends at a local branch.
- Maintain an in-memory cache of recently failed files to ignore duplicate error streams within a 5-minute window.

---

## Development Commands
- Run tests: `pytest`
- Lint code: `ruff check .`
- Format code: `ruff format .`

---

## Workflow Rules
- After completing a task, always create a git commit with a descriptive message summarizing what changed and why.
