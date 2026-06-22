"""Git operations module."""

import logging
import os
import subprocess
from datetime import datetime

from src.exceptions import GitOpsError

logger = logging.getLogger(__name__)


class GitOpsService:
    """Service for Git operations."""

    def clone_and_checkout(self, repo_url: str, branch: str | None) -> tuple[str, str]:
        """Clone a Git repository and checkout a specific branch."""
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        clone_path = os.path.realpath(f"/tmp/dataform-scout-{ts}")
        fix_branch = f"fix/dataform-{ts}"

        logger.info(f"Cloning {repo_url} into {clone_path}")
        try:
            subprocess.run(
                ["git", "clone", repo_url, clone_path],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            logger.error(f"Failed to clone repo: {exc.stderr}")
            raise GitOpsError(f"Clone failed: {exc.stderr}") from exc

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
