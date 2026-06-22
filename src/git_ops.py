import os
import subprocess
from datetime import datetime


def clone_and_checkout(repo_url: str, branch: str | None) -> tuple[str, str]:
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    clone_path = os.path.realpath(f"/tmp/dataform-scout-{ts}")
    fix_branch = f"fix/dataform-{ts}"

    subprocess.run(
        ["gh", "repo", "clone", repo_url, clone_path], check=True, capture_output=True
    )

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=clone_path, capture_output=True, text=True
    )
    if status.stdout.strip():
        print(f"[scout] Working directory {clone_path} is dirty. Aborting.")
        raise subprocess.CalledProcessError(1, "git status")

    if branch:
        try:
            subprocess.run(
                ["git", "checkout", branch],
                cwd=clone_path,
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError:
            pass

    subprocess.run(
        ["git", "checkout", "-b", fix_branch],
        cwd=clone_path,
        check=True,
        capture_output=True,
    )
    return fix_branch, clone_path
