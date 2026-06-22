FIXABLE_LLM_CODES: set[str] = {
    "invalidQuery",
    "syntaxError",
    "unrecognizedName",
    "unrecognized name",
    "fieldNotFound",
    "field not found",
    "typeMismatch",
    "type mismatch",
    "noMatchingSignature",
    "no matching signature",
    "invalidArgument",
    "invalid argument",
    "invalidFunctionArgument",
    "invalid function argument",
    "scalarSubqueryProducedMoreThanOneElement",
    "scalar subquery produced more than one element",
    "compilationError",
    "assertionFailed",
}

INFRA_CODES: set[str] = {
    "accessDenied",
    "quotaExceeded",
    "rateLimitExceeded",
    "backendError",
    "serviceUnavailable",
    "internalError",
    "timeout",
}

DONNEES_CODES: set[str] = {"invalidValue", "outOfRange", "jobFailed"}

INFRA_PATTERNS: list[str] = [
    "permission denied",
    "does not have permission",
    "dataset not found",
    "project not found",
    "quota",
    "credentials",
    "iam",
]


def detect_error_code(error_msg: str) -> str:  # noqa: C901
    reason_lower = (error_msg or "").lower()
    if "syntax error" in reason_lower:
        return "syntaxError"
    if (
        "access denied" in reason_lower
        or "permission denied" in reason_lower
        or "does not have permission" in reason_lower
    ):
        return "accessDenied"
    if "division by zero" in reason_lower:
        return "jobFailed"
    if "quota" in reason_lower:
        return "quotaExceeded"

    for code in FIXABLE_LLM_CODES:
        if code.lower() in reason_lower:
            return code
    for code in INFRA_CODES:
        if code.lower() in reason_lower:
            return code
    for code in DONNEES_CODES:
        if code.lower() in reason_lower:
            return code
    return "unknown"


def classify_error(error_code: str, error_msg: str) -> str:
    code_lower = (error_code or "").lower()
    msg_lower = (error_msg or "").lower()

    if code_lower in {c.lower() for c in FIXABLE_LLM_CODES}:
        return "FIXABLE_LLM"
    if code_lower in {c.lower() for c in INFRA_CODES}:
        return "INFRA"
    if code_lower in {c.lower() for c in DONNEES_CODES}:
        return "DATA"

    if any(p in msg_lower for p in INFRA_PATTERNS):
        return "INFRA"
    return "UNKNOWN"
