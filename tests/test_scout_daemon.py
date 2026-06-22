from unittest.mock import MagicMock, patch

from src.models import LogEntry
from src.scout_daemon import _extract_error_details, _handle_entry


def test_extract_error_details() -> None:
    raw_entry = {
        "jsonPayload": {
            "message": "syntax error near SELECT",
            "actionTarget": {"name": "my_dataset.my_view"},
        },
        "labels": {"action_name": "override_action"},
    }
    entry = LogEntry.from_dict(raw_entry)

    action_name, sqlx_path, error_msg = _extract_error_details(entry, raw_entry)
    assert action_name == "override_action"
    assert error_msg == "syntax error near SELECT"
    assert sqlx_path is None


@patch("src.scout_daemon.notify")
@patch("src.scout_daemon.trigger_claude_fix")
@patch("src.scout_daemon.clone_and_checkout")
@patch("src.scout_daemon.get_gcp_repo_url")
def test_handle_entry_fixable_error(
    mock_get_url: MagicMock, mock_clone: MagicMock, mock_trigger: MagicMock, mock_notify: MagicMock
) -> None:
    mock_get_url.return_value = "https://fake.repo.url"
    mock_clone.return_value = ("fix/branch", "/tmp/path")

    raw_entry = {
        "jsonPayload": {
            "message": "syntax error",
            "actionTarget": {"name": "test_action"},
        },
        "resource": {"labels": {"location": "eu", "repository_id": "test_repo"}},
        "logName": "projects/test-proj/logs/dataform",
    }

    _handle_entry(raw_entry)

    mock_get_url.assert_called_once_with("test-proj", "eu", "test_repo")
    mock_clone.assert_called_once_with("https://fake.repo.url", "")
    mock_trigger.assert_called_once_with(
        "test_action", None, "syntax error", "fix/branch", "/tmp/path"
    )


@patch("src.scout_daemon.notify")
@patch("src.scout_daemon.clone_and_checkout")
@patch("src.scout_daemon.get_gcp_repo_url")
def test_handle_entry_unfixable_error(
    mock_get_url: MagicMock, mock_clone: MagicMock, mock_notify: MagicMock
) -> None:
    mock_get_url.return_value = "https://fake.repo.url"

    raw_entry = {
        "jsonPayload": {"message": "permission denied"},
        "resource": {"labels": {"location": "eu", "repository_id": "test_repo"}},
        "logName": "projects/test-proj/logs/dataform",
    }

    _handle_entry(raw_entry)

    mock_get_url.assert_called_once()
    # Should not clone or trigger fix because permission denied is an INFRA error
    mock_clone.assert_not_called()
