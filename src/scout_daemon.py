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
from datetime import datetime, timezone, timedelta


GCLOUD = "gcloud"
PID_FILE = "/tmp/dataform-scout.pid"
CONFIG_FILE = os.path.expanduser("~/.config/dataform-scout/config")
LOG_FILTER = 'resource.type="dataform.googleapis.com/Repository" AND severity>=ERROR'
PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__))
)
SKILL_PATH = os.path.join(PLUGIN_ROOT, "skills", "fix-dataform", "SKILL.md")


FIXABLE_LLM_CODES = {
    "invalidQuery", "syntaxError", "unrecognizedName", "unrecognized name",
    "fieldNotFound", "field not found", "typeMismatch", "type mismatch",
    "noMatchingSignature", "no matching signature", "invalidArgument",
    "invalid argument", "invalidFunctionArgument", "invalid function argument",
    "scalarSubqueryProducedMoreThanOneElement", "scalar subquery produced more than one element",
    "compilationError", "assertionFailed",
}
INFRA_CODES = {"accessDenied", "quotaExceeded", "rateLimitExceeded", "backendError", "serviceUnavailable", "internalError", "timeout"}
DONNEES_CODES = {"invalidValue", "outOfRange", "jobFailed"}
INFRA_PATTERNS = ["permission denied", "does not have permission", "dataset not found", "project not found", "quota", "credentials", "iam"]


def detect_error_code(error_msg: str) -> str:
    reason_lower = (error_msg or "").lower()
    if "syntax error" in reason_lower: return "syntaxError"
    if "access denied" in reason_lower or "permission denied" in reason_lower or "does not have permission" in reason_lower: return "accessDenied"
    if "division by zero" in reason_lower: return "jobFailed"
    if "quota" in reason_lower: return "quotaExceeded"
    
    for code in FIXABLE_LLM_CODES:
        if code.lower() in reason_lower: return code
    for code in INFRA_CODES:
        if code.lower() in reason_lower: return code
    for code in DONNEES_CODES:
        if code.lower() in reason_lower: return code
    return "unknown"


def classify_error(error_code: str, error_msg: str) -> str:
    code_lower = (error_code or "").lower()
    msg_lower = (error_msg or "").lower()
    
    if code_lower in {c.lower() for c in FIXABLE_LLM_CODES}: return "FIXABLE_LLM"
    if code_lower in {c.lower() for c in INFRA_CODES}: return "INFRA"
    if code_lower in {c.lower() for c in DONNEES_CODES}: return "DATA"
    
    if any(p in msg_lower for p in INFRA_PATTERNS): return "INFRA"
    return "UNKNOWN"


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


def _extract_error_details(entry: dict) -> tuple[str | None, str | None, str | None]:
    """Return (action_name, sqlx_file_path, error_message) from a log entry."""
    payload = entry.get("jsonPayload") or entry.get("protoPayload") or {}
    text = entry.get("textPayload", "")

    error_msg = (
        payload.get("message") or payload.get("error") or text or json.dumps(payload)
    )

    action_name = None
    labels = entry.get("labels", {})
    if "action_name" in labels:
        action_name = labels["action_name"]
    elif "actionTarget" in payload and isinstance(payload["actionTarget"], dict):
        action_name = payload["actionTarget"].get("name")

    # Try to find a .sqlx path anywhere in the serialised entry
    raw = json.dumps(entry)
    match = re.search(r"[\w./-]+\.sqlx", raw)
    sqlx_path = match.group(0) if match else None

    return action_name, sqlx_path, error_msg


def _notify(title: str, message: str, subtitle: str = "", sound: str = "Basso") -> None:
    safe_title = title.replace('"', "'")
    safe_message = message.replace('"', "'")
    safe_subtitle = subtitle.replace('"', "'")
    subtitle_clause = f' subtitle "{safe_subtitle}"' if safe_subtitle else ""
    sound_clause = f' sound name "{sound}"' if sound else ""
    script = (
        f'display notification "{safe_message}"'
        f' with title "{safe_title}"'
        f"{subtitle_clause}"
        f"{sound_clause}"
    )
    subprocess.run(["/usr/bin/osascript", "-e", script], capture_output=True)


def _create_fix_branch() -> str:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    branch = f"fix/dataform-{ts}"
    subprocess.run(["git", "checkout", "-b", branch], check=True)
    return branch


def _trigger_claude_fix(action_name: str | None, sqlx_path: str | None, error_msg: str, branch: str):
    try:
        with open(SKILL_PATH) as f:
            system_prompt = f.read()
    except OSError as exc:
        print(f"[scout] Cannot read skill file {SKILL_PATH}: {exc}", file=sys.stderr)
        return

    prompt_lines = [
        f"Branch: {branch}",
        f"Error: {error_msg}",
    ]
    if action_name:
        prompt_lines.insert(0, f"Action: {action_name}")
    if sqlx_path:
        prompt_lines.insert(0, f"File: {sqlx_path}")

    prompt = "\n".join(prompt_lines)

    try:
        subprocess.run(
            ["claude", "--system-prompt", system_prompt, "-p", prompt],
            text=True,
            timeout=120,
        )
    except FileNotFoundError:
        print("[scout] WARNING: `claude` CLI not found.", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(
            "[scout] WARNING: claude fix attempt timed out after 120s.", file=sys.stderr
        )


def _handle_entry(entry: dict):
    action_name, sqlx_path, error_msg = _extract_error_details(entry)
    error_code = detect_error_code(error_msg)
    category = classify_error(error_code, error_msg)
    
    target_display = action_name or sqlx_path or "(unknown)"
    print(f"[scout] Error detected — target={target_display}, code={error_code}, category={category}")
    
    if category in ("INFRA", "DATA", "UNKNOWN"):
        print(f"[scout] Skipping non-fixable error: {category}")
        _notify(
            title="Dataform Scout",
            message=f"Skipped {category} error in {target_display}",
            subtitle=f"Code: {error_code}",
        )
        return

    _notify(
        title="Dataform Scout",
        message=f"Error in {target_display}",
        subtitle="Creating fix branch…",
    )
    try:
        branch = _create_fix_branch()
        print(f"[scout] Created branch: {branch}")
        _trigger_claude_fix(action_name, sqlx_path, error_msg, branch)
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
