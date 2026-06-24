"""Git operations module."""

import logging
import os
import subprocess
from datetime import datetime

from .exceptions import GitOpsError

logger = logging.getLogger(__name__)


class GitOpsService:
    """Service for Git operations."""

    def log_git_config(self) -> None:
        """Log all Git configuration."""
        try:
            result = subprocess.run(
                ["git", "config", "--list"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Git configuration:\n{result.stdout.strip()}")
        except subprocess.CalledProcessError as exc:
            logger.warning(f"Failed to retrieve git config: {exc.stderr}")

    def clone_and_checkout(self, repo_url: str, branch: str | None) -> tuple[str, str]:
        """Clone a Git repository and checkout a specific branch."""
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        clone_path = os.path.realpath(f"/tmp/dataform-scout-{ts}")
        fix_branch = f"fix/dataform-{ts}"

        logger.info(f"Cloning {repo_url} into {clone_path}")
        try:
            # ADR-0010: Use GitHub CLI (`gh`) instead of `git` to bypass
            # interactive authentication prompts for headless private repo cloning.
            subprocess.run(
                ["gh", "repo", "clone", repo_url, clone_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to clone repo: {exc.stderr}")
            raise GitOpsError(f"Clone failed: {exc.stderr}") from exc

        logger.info("Configuring local git credential helper...")
        try:
            subprocess.run(
                ["git", "config", "credential.helper", "!gh auth git-credential"],
                cwd=clone_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.warning(f"Failed to configure git credential helper: {exc.stderr}")

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=clone_path,
            capture_output=True,
            text=True,
        )
        if status.stdout.strip():
            logger.error(f"Working directory {clone_path} is dirty. Aborting.")
            raise GitOpsError(f"Working directory {clone_path} is dirty.")

        if branch:
            logger.info(f"Checking out target branch: {branch}")
            try:
                subprocess.run(
                    ["git", "checkout", branch],
                    cwd=clone_path,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as exc:
                logger.warning(
                    f"Could not checkout branch {branch}, "
                    f"it might not exist: {exc.stderr}"
                )

        logger.info(f"Creating fix branch: {fix_branch}")
        try:
            subprocess.run(
                ["git", "checkout", "-b", fix_branch],
                cwd=clone_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to create fix branch: {exc.stderr}")
            raise GitOpsError(f"Branch creation failed: {exc.stderr}") from exc

        return fix_branch, clone_path

    def push_and_create_pr(
        self, branch: str, wt_path: str, title: str, body: str
    ) -> None:
        """Push a local branch to the remote and open a Pull Request via gh."""
        logger.info(f"Pushing branch {branch} and creating PR.")
        try:
            subprocess.run(
                ["git", "push", "--set-upstream", "origin", branch],
                cwd=wt_path,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                ["gh", "pr", "create", "--title", title, "--body", body],
                cwd=wt_path,
                check=True,
                capture_output=True,
                text=True,
            )
            logger.info("Successfully pushed and created PR.")
        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to push or create PR: {exc.stderr}")
            raise GitOpsError(f"Failed to push or create PR: {exc.stderr}") from exc
