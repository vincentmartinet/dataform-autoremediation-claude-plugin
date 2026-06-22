"""Module for invoking headless Claude Code logic."""

import logging
import subprocess

from .constants import MAX_FIX_ATTEMPTS, SKILL_PATH
from .notifications import NotificationService

logger = logging.getLogger(__name__)


class ClaudeInvokerService:
    """Service for invoking headless Claude Code logic."""

    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service

    def trigger_claude_fix(
        self,
        action_name: str | None,
        sqlx_path: str | None,
        error_msg: str,
        branch: str,
        wt_path: str,
    ) -> None:
        """Triggers a headless Claude Code session to apply automated fixes."""
        try:
            with open(SKILL_PATH) as f:
                system_prompt = f.read()
        except OSError as exc:
            logger.error(f"Cannot read skill file {SKILL_PATH}: {exc}")
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

        for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
            logger.info(f"Claude fix attempt {attempt}/{MAX_FIX_ATTEMPTS}...")
            try:
                subprocess.run(
                    [
                        "claude",
                        "--system-prompt",
                        system_prompt,
                        "--permission-mode",
                        "auto",
                        "-p",
                        prompt,
                    ],
                    text=True,
                    timeout=120,
                    cwd=wt_path,
                )

                compile_res = subprocess.run(
                    ["dataform", "compile"], cwd=wt_path, capture_output=True, text=True
                )
                if compile_res.returncode == 0:
                    logger.info(f"Fix successful on attempt {attempt}.")
                    self.notification_service.notify(
                        "Dataform Scout",
                        "Fix successful!",
                        f"Compiled successfully on attempt {attempt}",
                    )
                    return
                else:
                    prompt = (
                        "The previous fix did not resolve the error. Dataform compile output:\n"  # noqa: E501
                        f"{compile_res.stderr}\nPlease try again."
                    )
            except FileNotFoundError:
                logger.warning("`claude` CLI not found.")
                return
            except subprocess.TimeoutExpired:
                logger.warning(f"claude fix attempt {attempt} timed out after 120s.")
                prompt = (
                    "The previous fix attempt timed out. "
                    "Please be more concise and try again."
                )

        logger.error(f"Failed to fix after {MAX_FIX_ATTEMPTS} attempts. Reverting.")
        subprocess.run(["git", "checkout", "."], cwd=wt_path, capture_output=True)
        subprocess.run(["git", "checkout", "-"], cwd=wt_path, capture_output=True)
        subprocess.run(
            ["git", "branch", "-D", branch], cwd=wt_path, capture_output=True
        )
        self.notification_service.notify(
            "Dataform Scout",
            "Auto-fix failed",
            f"Could not fix after {MAX_FIX_ATTEMPTS} attempts. Reverted changes.",
        )
