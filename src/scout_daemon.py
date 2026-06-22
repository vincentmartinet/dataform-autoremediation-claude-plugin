#!/usr/bin/env python3
"""
Dataform Scout Daemon — monitors GCP Dataform error logs and triggers Claude Code fixes.
Relies entirely on the active `gcloud` configuration. Never pushes to remote.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import datetime, timezone, timedelta

from constants import CONFIG_FILE, GCLOUD, LOG_FILTER, PID_FILE
from models import LogEntry
from error_classification import detect_error_code, classify_error
from gcp_api import (
    get_gcp_repo_url,
    fetch_workflow_branch,
    fetch_workflow_failed_actions,
)
from git_ops import clone_and_checkout
from claude_invoker import trigger_claude_fix
from notifications import notify

_recent_failures: dict[str, datetime] = {}


def _load_scope_flags() -> list[str]:
    if not os.path.exists(CONFIG_FILE):
        return []
    cfg: dict[str, str] = {}
    with open(CONFIG_FILE) as f:
        for line in f:
            line = line.strip()
            if "=" in line:
                k, _, v = line.partition("=")
                cfg[k.strip()] = v.strip()
    scope_type = cfg.get("scope_type", "")
    scope_id = cfg.get("scope_id", "")
    if not scope_type or not scope_id:
        return []
    flag_map = {
        "project": "--project",
        "folder": "--folder",
        "organization": "--organization",
    }
    flag = flag_map.get(scope_type)
    return [flag, scope_id] if flag else []


SCOPE_FLAGS = _load_scope_flags()
_tail_proc = None


def _graceful_exit(signum, frame):
    if _tail_proc and _tail_proc.poll() is None:
        _tail_proc.terminate()
    try:
        os.unlink(PID_FILE)
    except OSError:
        pass
    sys.exit(0)


signal.signal(signal.SIGINT, _graceful_exit)
signal.signal(signal.SIGTERM, _graceful_exit)


def _extract_error_details(
    entry: LogEntry, raw_entry: dict
) -> tuple[str | None, str | None, str | None]:
    """Return (action_name, sqlx_file_path, error_message) from a log entry."""
    payload = entry.jsonPayload or entry.protoPayload or {}
    text = entry.textPayload

    error_msg = (
        payload.get("message") or payload.get("error") or text or json.dumps(payload)
    )

    action_name = None
    if "action_name" in entry.labels:
        action_name = entry.labels["action_name"]
    elif "actionTarget" in payload and isinstance(payload["actionTarget"], dict):
        action_name = payload["actionTarget"].get("name")

    # Try to find a .sqlx path anywhere in the serialised entry
    raw = json.dumps(raw_entry)
    match = re.search(r"[\w./-]+\.sqlx", raw)
    sqlx_path = match.group(0) if match else None

    return action_name, sqlx_path, error_msg


def _process_error_context(
    action_name: str | None,
    sqlx_path: str | None,
    error_msg: str,
    project_id: str,
    location: str,
    repository_id: str,
    branch: str | None,
):
    repo_url = get_gcp_repo_url(project_id, location, repository_id)
    if not repo_url:
        print(
            f"[scout] Could not deduce Git remote URL for {project_id}/{repository_id}. Skipping."
        )
        return

    error_code = detect_error_code(error_msg)
    category = classify_error(error_code, error_msg)

    target_display = action_name or sqlx_path or "(unknown)"
    print(
        f"[scout] Error detected — target={target_display}, code={error_code}, category={category}"
    )

    if category in ("INFRA", "DATA", "UNKNOWN"):
        print(f"[scout] Skipping non-fixable error: {category}")
        notify(
            title="Dataform Scout",
            message=f"Skipped {category} error in {target_display}",
            subtitle=f"Code: {error_code}",
        )
        return

    notify(
        title="Dataform Scout",
        message=f"Error in {target_display}",
        subtitle="Cloning repository for fix…",
    )
    try:
        fix_branch, clone_path = clone_and_checkout(repo_url, branch)
        print(f"[scout] Cloned to {clone_path} on branch {fix_branch}")
        trigger_claude_fix(action_name, sqlx_path, error_msg, fix_branch, clone_path)
    except subprocess.CalledProcessError as exc:
        print(f"[scout] git error: {exc}", file=sys.stderr)


def _handle_entry(raw_entry: dict):
    global _recent_failures
    try:
        entry = LogEntry.from_dict(raw_entry)
        payload = entry.jsonPayload or entry.protoPayload or {}
        type_str = payload.get("@type", "")

        location = entry.resource.get("labels", {}).get("location", "")
        repository_id = entry.resource.get("labels", {}).get("repository_id", "")

        project_id = (
            entry.logName.split("/")[1] if entry.logName.startswith("projects/") else ""
        )
        workspace_id = entry.labels.get("workspace_id")

        if (
            type_str
            == "type.googleapis.com/google.cloud.dataform.logging.v1.WorkflowInvocationCompletionLogEntry"
        ):
            if payload.get("terminalState") == "FAILED":
                invocation_id = payload.get("workflowInvocationId")

                if invocation_id and location and repository_id and project_id:
                    print(
                        f"[scout] Fetching failed actions for invocation {invocation_id}..."
                    )
                    failed_actions = fetch_workflow_failed_actions(
                        project_id, location, repository_id, invocation_id
                    )
                    branch = fetch_workflow_branch(
                        project_id, location, repository_id, invocation_id
                    )
                    for action in failed_actions:
                        action_name = action.get("target", {}).get("name")
                        error_msg = action.get("failureReason", "")

                        cache_key = f"{project_id}:{repository_id}:{action_name}"
                        now = datetime.now()
                        if (
                            cache_key in _recent_failures
                            and (now - _recent_failures[cache_key]).total_seconds()
                            < 300
                        ):
                            continue
                        _recent_failures[cache_key] = now

                        _process_error_context(
                            action_name,
                            None,
                            error_msg,
                            project_id,
                            location,
                            repository_id,
                            branch,
                        )
                    return

        action_name, sqlx_path, error_msg = _extract_error_details(entry, raw_entry)

        cache_key = f"{project_id}:{repository_id}:{sqlx_path or action_name}"
        now = datetime.now()
        if (
            cache_key in _recent_failures
            and (now - _recent_failures[cache_key]).total_seconds() < 300
        ):
            return
        _recent_failures[cache_key] = now

        _process_error_context(
            action_name,
            sqlx_path,
            error_msg,
            project_id,
            location,
            repository_id,
            workspace_id,
        )
    except Exception as e:
        print(f"[scout] Error handling entry: {e}", file=sys.stderr)


def _lookback():
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    full_filter = f'{LOG_FILTER} AND timestamp>="{since}"'
    print("[scout] Running 24-hour lookback…")
    result = subprocess.run(
        [GCLOUD, "logging", "read", full_filter, "--format=json"] + SCOPE_FLAGS,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"[scout] gcloud error: {result.stderr.strip()}", file=sys.stderr)
        return
    try:
        entries = json.loads(result.stdout or "[]")
    except json.JSONDecodeError:
        print("[scout] Failed to parse lookback output.", file=sys.stderr)
        return
    print(f"[scout] Found {len(entries)} error(s) in the last 24 hours.")
    for entry in entries:
        _handle_entry(entry)


def _stream():
    global _tail_proc
    print("[scout] Starting real-time log stream (Ctrl-C to stop)…")
    _tail_proc = subprocess.Popen(
        [GCLOUD, "alpha", "logging", "tail", LOG_FILTER, "--format=json"] + SCOPE_FLAGS,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    buffer = ""
    for line in _tail_proc.stdout:
        buffer += line
        try:
            entry = json.loads(buffer)
            buffer = ""
            _handle_entry(entry)
        except json.JSONDecodeError:
            pass  # accumulate multi-line JSON


def check_dependencies():
    missing = []
    for cmd in ["gcloud", "git", "dataform", "gh"]:
        if shutil.which(cmd) is None:
            missing.append(cmd)
    if missing:
        print(
            f"[scout] Error: Missing required executables in PATH: {', '.join(missing)}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    check_dependencies()
    _lookback()
    _stream()
