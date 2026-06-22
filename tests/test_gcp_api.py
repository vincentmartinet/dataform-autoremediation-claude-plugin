import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.gcp_api import (
    fetch_workflow_branch,
    fetch_workflow_failed_actions,
    get_gcp_repo_url,
)


@pytest.fixture
def mock_token() -> Any:
    with patch("src.gcp_api.subprocess.run") as mock_run:
        mock_run.return_value.stdout = "fake_token"
        yield mock_run


@patch("src.gcp_api.urllib.request.urlopen")
def test_get_gcp_repo_url_success(mock_urlopen: MagicMock, mock_token: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "gitRemoteSettings": {"url": "https://source.developers.google.com/p/my-proj/r/my-repo"}
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    url = get_gcp_repo_url("my-proj", "eu", "my-repo")
    assert url == "https://source.developers.google.com/p/my-proj/r/my-repo"


@patch("src.gcp_api.urllib.request.urlopen")
def test_fetch_workflow_branch(mock_urlopen: MagicMock, mock_token: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "invocationConfig": {"gitCommitish": "my-feature-branch"}
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    branch = fetch_workflow_branch("my-proj", "eu", "my-repo", "inv-123")
    assert branch == "my-feature-branch"


@patch("src.gcp_api.urllib.request.urlopen")
def test_fetch_workflow_failed_actions(mock_urlopen: MagicMock, mock_token: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps({
        "workflowInvocationActions": [
            {"state": "SUCCEEDED", "target": {"name": "action1"}},
            {"state": "FAILED", "target": {"name": "action2"}, "failureReason": "syntax error"},
        ]
    }).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    failed = fetch_workflow_failed_actions("my-proj", "eu", "my-repo", "inv-123")
    assert len(failed) == 1
    assert failed[0]["target"]["name"] == "action2"
    assert failed[0]["failureReason"] == "syntax error"
