import subprocess
from unittest.mock import MagicMock, patch

import pytest

from src.exceptions import GitOpsError
from src.git_ops import GitOpsService


@patch("src.git_ops.subprocess.run")
def test_clone_and_checkout_success(mock_run: MagicMock) -> None:
    # Mock successful git clone and git status (clean)
    mock_run.return_value.stdout = ""
    mock_run.return_value.returncode = 0

    git_ops = GitOpsService()
    fix_branch, clone_path = git_ops.clone_and_checkout("https://fake.url", "main")

    assert fix_branch.startswith("fix/dataform-")
    assert "/tmp/dataform-scout-" in clone_path

    # Verify subprocess calls
    assert mock_run.call_count == 4
    calls = mock_run.call_args_list

    # 1. clone
    assert "clone" in calls[0][0][0]
    assert calls[0][0][0][2] == "https://fake.url"

    # 2. status
    assert "status" in calls[1][0][0]

    # 3. checkout branch
    assert "checkout" in calls[2][0][0]
    assert calls[2][0][0][2] == "main"

    # 4. checkout -b fix_branch
    assert "-b" in calls[3][0][0]


@patch("src.git_ops.subprocess.run")
def test_clone_and_checkout_dirty_dir(mock_run: MagicMock) -> None:
    # Mock dirty status
    mock_run.side_effect = [
        subprocess.CompletedProcess(args=[], returncode=0, stdout=""),  # clone
        subprocess.CompletedProcess(
            args=[], returncode=0, stdout=" M some_file.py\n"
        ),  # status
    ]

    git_ops = GitOpsService()
    with pytest.raises(GitOpsError) as exc_info:
        git_ops.clone_and_checkout("https://fake.url", None)

    assert "is dirty" in str(exc_info.value)


@patch("src.git_ops.subprocess.run")
def test_clone_and_checkout_clone_failure(mock_run: MagicMock) -> None:
    mock_run.side_effect = subprocess.CalledProcessError(
        1, "git", stderr="clone failed"
    )

    git_ops = GitOpsService()
    with pytest.raises(GitOpsError) as exc_info:
        git_ops.clone_and_checkout("https://fake.url", None)

    assert "Clone failed" in str(exc_info.value)
