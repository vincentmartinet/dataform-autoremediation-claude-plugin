import typing

from src.models import LogEntry


def test_log_entry_from_dict_json_payload(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    data = {
        "jsonPayload": {
            "message": "test error",
            "actionTarget": {"name": "test_action"},
        },
        "logName": "projects/my-project/logs/test",
    }

    entry = LogEntry.from_dict(data)
    assert entry.payload.message == "test error"
    assert entry.payload.action_target is not None
    assert entry.payload.action_target.name == "test_action"
    assert entry.project_id == "my-project"


def test_log_entry_from_dict_proto_payload(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    data = {
        "protoPayload": {"@type": "type.googleapis.com/test", "error": "proto error"},
        "textPayload": "fallback text",
    }

    entry = LogEntry.from_dict(data)
    assert entry.payload.error == "proto error"
    assert entry.payload.type_str == "type.googleapis.com/test"
    assert entry.text_payload == "fallback text"


def test_log_entry_from_dict_empty(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    entry = LogEntry.from_dict({})
    assert entry.text_payload == ""
    assert entry.payload.message == ""
    assert entry.project_id == ""
