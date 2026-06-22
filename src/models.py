from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class LogEntry:
    jsonPayload: Optional[Dict[str, Any]] = None
    protoPayload: Optional[Dict[str, Any]] = None
    textPayload: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    resource: Dict[str, Any] = field(default_factory=dict)
    logName: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "LogEntry":
        return cls(
            jsonPayload=data.get("jsonPayload"),
            protoPayload=data.get("protoPayload"),
            textPayload=data.get("textPayload", ""),
            labels=data.get("labels", {}),
            resource=data.get("resource", {}),
            logName=data.get("logName", ""),
        )
