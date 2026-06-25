from unittest.mock import ANY, MagicMock

from src.models import LogEntry
from src.scout_daemon import ScoutDaemon


def get_mocked_daemon() -> ScoutDaemon:
    return ScoutDaemon(
        gcp_client=MagicMock(),
        git_ops=MagicMock(),
        invoker=MagicMock(),
        notification_service=MagicMock(),
        error_classifier=MagicMock(),
    )


def test_extract_error_details() -> None:
    raw_entry = {
        "jsonPayload": {
            "message": "syntax error near SELECT",
            "actionTarget": {"name": "my_dataset.my_view"},
        },
        "labels": {"action_name": "override_action"},
    }
    entry = LogEntry.from_dict(raw_entry)

    daemon = get_mocked_daemon()
    action_name, sqlx_path, error_msg = daemon._extract_error_details(entry, raw_entry)
    assert action_name == "override_action"
    assert error_msg == "syntax error near SELECT"
    assert sqlx_path is None


def test_handle_entry_fixable_error() -> None:
    daemon = get_mocked_daemon()
    daemon.gcp_client.get_gcp_repo_url.return_value = "https://fake.repo.url"
    daemon.git_ops.clone_and_checkout.return_value = "fix/branch"
    # For a fixable error, detect_error_code could return "syntaxError"
    # and classify_error returns "FIXABLE_LLM"
    daemon.error_classifier.detect_error_code.return_value = "syntaxError"
    daemon.error_classifier.classify_error.return_value = "FIXABLE_LLM"

    raw_entry = {
        "jsonPayload": {
            "message": "syntax error",
            "actionTarget": {"name": "test_action"},
        },
        "resource": {"labels": {"location": "eu", "repository_id": "test_repo"}},
        "logName": "projects/test-proj/logs/dataform",
    }

    daemon._handle_entry(raw_entry)

    daemon.gcp_client.get_gcp_repo_url.assert_called_once_with(
        "test-proj", "eu", "test_repo"
    )
    daemon.git_ops.clone_and_checkout.assert_called_once_with(
        "https://fake.repo.url", "", ANY
    )
    daemon.invoker.trigger_claude_fix.assert_called_once_with(
        "test_action", None, "syntax error", "fix/branch", ANY
    )


def test_handle_entry_unfixable_error() -> None:
    daemon = get_mocked_daemon()
    daemon.gcp_client.get_gcp_repo_url.return_value = "https://fake.repo.url"
    daemon.error_classifier.detect_error_code.return_value = "accessDenied"
    daemon.error_classifier.classify_error.return_value = "INFRA"

    raw_entry = {
        "jsonPayload": {"message": "permission denied"},
        "resource": {"labels": {"location": "eu", "repository_id": "test_repo"}},
        "logName": "projects/test-proj/logs/dataform",
    }

    daemon._handle_entry(raw_entry)

    daemon.gcp_client.get_gcp_repo_url.assert_called_once()
    # Should not clone or trigger fix because permission denied is an INFRA error
    daemon.git_ops.clone_and_checkout.assert_not_called()
