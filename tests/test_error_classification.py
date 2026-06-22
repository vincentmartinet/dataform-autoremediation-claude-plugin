import typing

from src.error_classification import classify_error, detect_error_code


def test_detect_error_code(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    assert detect_error_code("this is a syntax error here") == "syntaxError"
    assert detect_error_code("permission denied to table") == "accessDenied"
    assert detect_error_code("division by zero error") == "jobFailed"
    assert detect_error_code("quota exceeded for project") == "quotaExceeded"
    assert detect_error_code("unrecognized name: col1") == "unrecognized name"
    assert detect_error_code("some random unknown error") == "unknown"


def test_classify_error(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    assert classify_error("syntaxError", "") == "FIXABLE_LLM"
    assert classify_error("accessDenied", "") == "INFRA"
    assert classify_error("jobFailed", "") == "DATA"

    # Test pattern matching
    assert classify_error("unknown", "user does not have permission") == "INFRA"
    assert classify_error("unknown", "random stuff") == "UNKNOWN"
