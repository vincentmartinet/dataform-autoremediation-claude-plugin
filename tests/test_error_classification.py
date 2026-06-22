import typing

from src.error_classification import ErrorClassifier


def test_detect_error_code(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    classifier = ErrorClassifier()
    assert classifier.detect_error_code("this is a syntax error here") == "syntaxError"
    assert classifier.detect_error_code("permission denied to table") == "accessDenied"
    assert classifier.detect_error_code("division by zero error") == "jobFailed"
    assert classifier.detect_error_code("quota exceeded for project") == "quotaExceeded"
    assert (
        classifier.detect_error_code("unrecognized name: col1") == "unrecognized name"
    )
    assert classifier.detect_error_code("some random unknown error") == "unknown"


def test_classify_error(
    mock_run: typing.Any = None,
    mock_get_url: typing.Any = None,
    mock_clone: typing.Any = None,
    mock_trigger: typing.Any = None,
    mock_urlopen: typing.Any = None,
    mock_token: typing.Any = None,
) -> None:
    classifier = ErrorClassifier()
    assert classifier.classify_error("syntaxError", "") == "FIXABLE_LLM"
    assert classifier.classify_error("accessDenied", "") == "INFRA"
    assert classifier.classify_error("jobFailed", "") == "DATA"

    # Test pattern matching
    assert (
        classifier.classify_error("unknown", "user does not have permission") == "INFRA"
    )
    assert classifier.classify_error("unknown", "random stuff") == "UNKNOWN"
