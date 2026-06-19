#!/usr/bin/env python3
"""
Dataform Scout Daemon — monitors GCP Dataform error logs and triggers Claude Code fixes.
Relies entirely on the active `gcloud` configuration. Never pushes to remote.
"""

import json
import os
import re
import signal
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta


GCLOUD = "gcloud"
PID_FILE = "/tmp/dataform-scout.pid"
CONFIG_FILE = os.path.expanduser("~/.config/dataform-scout/config")
LOG_FILTER = 'resource.type="dataform.googleapis.com/Repository" ' "AND severity=ERROR"
PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__))
)
SKILL_PATH = os.path.join(PLUGIN_ROOT, "src", "skills", "fix_dataform.md")


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


def _extract_error_details(entry: dict) -> tuple[str | None, str | None]:
    """Return (sqlx_file_path, error_message) from a log entry, or (None, None)."""
    payload = entry.get("jsonPayload") or {}
    text = entry.get("textPayload", "")

    error_msg = (
        payload.get("message") or payload.get("error") or text or json.dumps(payload)
    )

    # Try to find a .sqlx path anywhere in the serialised entry
    raw = json.dumps(entry)
    match = re.search(r"[\w./-]+\.sqlx", raw)
    sqlx_path = match.group(0) if match else None

    return sqlx_path, error_msg


def _create_fix_branch() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = f"fix/dataform-{ts}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    return branch


def _trigger_claude_fix(sqlx_path: str | None, error_msg: str, branch: str):
    prompt_lines = [
        f"Skill: {SKILL_PATH}",
        "",
        f"Branch: {branch}",
        f"Error: {error_msg}",
    ]
    if sqlx_path:
        prompt_lines.insert(2, f"File: {sqlx_path}")

    prompt = "\n".join(prompt_lines)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        subprocess.run(["claude", "-p", prompt], input=prompt, text=True)
    except FileNotFoundError:
        print(
            "[scout] WARNING: `claude` CLI not found. Prompt written to:", prompt_file
        )
    finally:
        try:
            os.unlink(prompt_file)
        except OSError:
            pass


def _handle_entry(entry: dict):
    sqlx_path, error_msg = _extract_error_details(entry)
    print(f"[scout] Error detected — file={sqlx_path or '(unknown)'}")
    try:
        branch = _create_fix_branch()
        print(f"[scout] Created branch: {branch}")
        _trigger_claude_fix(sqlx_path, error_msg, branch)
    except subprocess.CalledProcessError as exc:
        print(f"[scout] git error: {exc}", file=sys.stderr)


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


if __name__ == "__main__":
    _lookback()
    _stream()
