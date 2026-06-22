#!/usr/bin/env python3
"""Dataform Scout Daemon.

Monitors GCP Dataform error logs and triggers Claude Code fixes.
Relies entirely on the active `gcloud` configuration. Never pushes to remote.
"""

import contextlib
import json
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

from .claude_invoker import ClaudeInvokerService
from .constants import CONFIG_FILE, GCLOUD, LOG_FILTER, PID_FILE
from .error_classification import ErrorClassifier
from .exceptions import GitOpsError, MissingDependencyError
from .gcp_api import GCPApiClient
from .git_ops import GitOpsService
from .models import LogEntry
from .notifications import NotificationService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("scout_daemon")


class ScoutDaemon:
    """Main daemon for Dataform Scout."""

    def __init__(
        self,
        gcp_client: GCPApiClient,
        git_ops: GitOpsService,
        invoker: ClaudeInvokerService,
        notification_service: NotificationService,
        error_classifier: ErrorClassifier,
    ):
        """Initialize the ScoutDaemon."""
        self.gcp_client = gcp_client
        self.git_ops = git_ops
        self.invoker = invoker
        self.notification_service = notification_service
        self.error_classifier = error_classifier

        self._recent_failures: dict[str, datetime] = {}
        self.scope_flags = self._load_scope_flags()
        self._tail_proc: subprocess.Popen[str] | None = None

        signal.signal(signal.SIGINT, self._graceful_exit)
        signal.signal(signal.SIGTERM, self._graceful_exit)

    def _clean_cache(self) -> None:
        now = datetime.now()
        self._recent_failures = {
            k: v
            for k, v in self._recent_failures.items()
            if (now - v).total_seconds() < 300
        }

    def _load_scope_flags(self) -> list[str]:
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

    def _graceful_exit(self, signum: Any, frame: Any) -> None:
        logger.info("Shutting down daemon...")
        if self._tail_proc and self._tail_proc.poll() is None:
            self._tail_proc.terminate()
        with contextlib.suppress(OSError):
            os.unlink(PID_FILE)
        sys.exit(0)

    def _extract_error_details(
        self, entry: LogEntry, raw_entry: dict[str, Any]
    ) -> tuple[str | None, str | None, str]:
        """Return (action_name, sqlx_file_path, error_message) from a log entry."""
        payload = entry.payload
        text = entry.text_payload

        error_msg = (
            payload.message or payload.error or text or json.dumps(payload.raw_data)
        )

        action_name = None
        if entry.labels.action_name:
            action_name = entry.labels.action_name
        elif payload.action_target and payload.action_target.name:
            action_name = payload.action_target.name

        raw = json.dumps(raw_entry)
        match = re.search(r"[\w./-]+\.sqlx", raw)
        sqlx_path = match.group(0) if match else None

        return action_name, sqlx_path, error_msg

    def _process_error_context(
        self,
        action_name: str | None,
        sqlx_path: str | None,
        error_msg: str,
        project_id: str,
        location: str,
        repository_id: str,
        branch: str | None,
        timestamp: str,
    ) -> None:
        repo_url = self.gcp_client.get_gcp_repo_url(project_id, location, repository_id)
        if not repo_url:
            logger.warning(
                f"Could not deduce Git remote URL for {project_id}/{repository_id}. "
                "Skipping."
            )
            return

        error_code = self.error_classifier.detect_error_code(error_msg)
        category = self.error_classifier.classify_error(error_code, error_msg)

        target_display = action_name or sqlx_path or "(unknown)"
        logger.info(
            f"[{timestamp}] Caught {error_code} on {target_display} "
            f"in repo {repository_id}... category={category}"
        )

        if category in ("INFRA", "DATA", "UNKNOWN"):
            logger.info(f"Skipping non-fixable error: {category}")
            self.notification_service.notify(
                title="Dataform Scout",
                message=f"Skipped {category} error in {target_display}",
                subtitle=f"Code: {error_code}",
            )
            return

        self.notification_service.notify(
            title="Dataform Scout",
            message=f"Error in {target_display}",
            subtitle="Cloning repository for fix…",
        )
        try:
            fix_branch, clone_path = self.git_ops.clone_and_checkout(repo_url, branch)
            logger.info(f"Cloned to {clone_path} on branch {fix_branch}")
            self.invoker.trigger_claude_fix(
                action_name, sqlx_path, error_msg, fix_branch, clone_path
            )
        except GitOpsError as exc:
            logger.error(f"Git operation failed: {exc}")

    def _handle_entry(self, raw_entry: dict[str, Any]) -> None:
        self._clean_cache()

        try:
            entry = LogEntry.from_dict(raw_entry)
            type_str = entry.payload.type_str

            location = entry.resource.labels.location
            repository_id = entry.resource.labels.repository_id
            project_id = entry.project_id
            workspace_id = entry.labels.workspace_id

            is_workflow = (
                type_str == "type.googleapis.com/google.cloud.dataform.logging.v1."
                "WorkflowInvocationCompletionLogEntry"
            )
            if is_workflow and entry.payload.terminal_state == "FAILED":
                invocation_id = entry.payload.workflow_invocation_id

                if invocation_id and location and repository_id and project_id:
                    logger.info(
                        f"Fetching failed actions for invocation {invocation_id}..."
                    )
                    failed_actions = self.gcp_client.fetch_workflow_failed_actions(
                        project_id, location, repository_id, invocation_id
                    )
                    branch = self.gcp_client.fetch_workflow_branch(
                        project_id, location, repository_id, invocation_id
                    )
                    for action in failed_actions:
                        target = action.get("target", {})
                        if isinstance(target, dict):
                            action_name = target.get("name", "")
                        else:
                            action_name = ""
                        error_msg = str(action.get("failureReason", ""))

                        cache_key = f"{project_id}:{repository_id}:{action_name}"
                        now = datetime.now()
                        if cache_key in self._recent_failures:
                            continue
                        self._recent_failures[cache_key] = now

                        self._process_error_context(
                            action_name,
                            None,
                            error_msg,
                            project_id,
                            location,
                            repository_id,
                            branch,
                            entry.timestamp,
                        )
                    return

            action_name, sqlx_path, error_msg = self._extract_error_details(
                entry, raw_entry
            )

            cache_key = f"{project_id}:{repository_id}:{sqlx_path or action_name}"
            now = datetime.now()
            if cache_key in self._recent_failures:
                return
            self._recent_failures[cache_key] = now

            self._process_error_context(
                action_name,
                sqlx_path,
                error_msg,
                project_id,
                location,
                repository_id,
                workspace_id,
                entry.timestamp,
            )
        except Exception as e:
            logger.error(f"Error handling entry: {e}", exc_info=True)

    def _lookback(self) -> None:
        since = (datetime.now(UTC) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
        full_filter = f'{LOG_FILTER} AND timestamp>="{since}"'
        logger.info("Running 24-hour lookback…")

        cmd = [
            GCLOUD,
            "logging",
            "read",
            full_filter,
            "--format=json",
        ] + self.scope_flags
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"gcloud lookback error: {result.stderr.strip()}")
            return

        try:
            entries = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            logger.error("Failed to parse lookback output.")
            return

        logger.info(f"Found {len(entries)} error(s) in the last 24 hours.")
        for entry in entries:
            if isinstance(entry, dict):
                self._handle_entry(entry)

    def _stream(self) -> None:
        logger.info("Starting real-time log stream (Ctrl-C to stop)…")

        cmd = [
            GCLOUD,
            "alpha",
            "logging",
            "tail",
            LOG_FILTER,
            "--format=json",
        ] + self.scope_flags
        self._tail_proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        buffer = ""
        if self._tail_proc.stdout is None:
            return

        for line in self._tail_proc.stdout:
            buffer += line
            try:
                entry = json.loads(buffer)
                buffer = ""
                if isinstance(entry, dict):
                    self._handle_entry(entry)
            except json.JSONDecodeError:
                pass

    def check_dependencies(self) -> None:
        """Check if required external CLI tools are installed."""
        missing = []
        for cmd in ["gcloud", "git", "dataform", "gh"]:
            if shutil.which(cmd) is None:
                missing.append(cmd)
        if missing:
            msg = f"Missing required executables in PATH: {', '.join(missing)}"
            logger.error(msg)
            raise MissingDependencyError(msg)

    def run(self) -> None:
        """Run the scout daemon."""
        self.check_dependencies()
        self._lookback()
        self._stream()


if __name__ == "__main__":
    try:
        notification_service = NotificationService()
        gcp_client = GCPApiClient()
        git_ops = GitOpsService()
        invoker = ClaudeInvokerService(notification_service, git_ops)
        error_classifier = ErrorClassifier()

        daemon = ScoutDaemon(
            gcp_client=gcp_client,
            git_ops=git_ops,
            invoker=invoker,
            notification_service=notification_service,
            error_classifier=error_classifier,
        )
        daemon.run()
    except MissingDependencyError:
        sys.exit(1)
