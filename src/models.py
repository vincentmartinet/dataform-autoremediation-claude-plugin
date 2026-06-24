"""Data models for log entries and payload."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ActionTarget:
    """Action target from log payload."""

    name: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ActionTarget":
        """Create ActionTarget from dictionary."""
        if not isinstance(data, dict):
            return cls()
        return cls(name=data.get("name", ""))


@dataclass
class Payload:
    """Payload structure from log entry."""

    message: str = ""
    error: str = ""
    type_str: str = ""
    terminal_state: str = ""
    workflow_invocation_id: str = ""
    action_target: ActionTarget | None = None
    raw_data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "Payload":
        """Create Payload from dictionary."""
        if not data or not isinstance(data, dict):
            return cls()

        target_data = data.get("actionTarget") or data.get("action_target")
        target = ActionTarget.from_dict(target_data) if target_data else None

        return cls(
            message=data.get("message", ""),
            error=data.get("error", ""),
            type_str=data.get("@type", ""),
            terminal_state=data.get("terminalState") or data.get("terminal_state", ""),
            workflow_invocation_id=data.get("workflowInvocationId")
            or data.get("workflow_invocation_id", ""),
            action_target=target,
            raw_data=data,
        )


@dataclass
class ResourceLabels:
    """Labels from log resource."""

    location: str = ""
    repository_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResourceLabels":
        """Create ResourceLabels from dictionary."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            location=data.get("location", ""),
            repository_id=data.get("repository_id", ""),
        )


@dataclass
class Resource:
    """Resource structure from log entry."""

    labels: ResourceLabels = field(default_factory=ResourceLabels)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Resource":
        """Create Resource from dictionary."""
        if not isinstance(data, dict):
            return cls()
        return cls(labels=ResourceLabels.from_dict(data.get("labels", {})))


@dataclass
class LogEntryLabels:
    """Labels from log entry."""

    action_name: str = ""
    workspace_id: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntryLabels":
        """Create LogEntryLabels from dictionary."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            action_name=data.get("action_name", ""),
            workspace_id=data.get("workspace_id", ""),
        )


@dataclass
class LogEntry:
    """Top-level Google Cloud logging entry."""

    text_payload: str = ""
    payload: Payload = field(default_factory=Payload)
    labels: LogEntryLabels = field(default_factory=LogEntryLabels)
    resource: Resource = field(default_factory=Resource)
    log_name: str = ""
    timestamp: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEntry":
        """Create LogEntry from dictionary."""
        raw_json = data.get("jsonPayload") or data.get("json_payload")
        raw_proto = data.get("protoPayload") or data.get("proto_payload")

        # Use jsonPayload if available, else protoPayload, else empty
        payload_data = (
            raw_json
            if isinstance(raw_json, dict)
            else (raw_proto if isinstance(raw_proto, dict) else {})
        )

        return cls(
            text_payload=data.get("textPayload") or data.get("text_payload", ""),
            payload=Payload.from_dict(payload_data),
            labels=LogEntryLabels.from_dict(data.get("labels", {})),
            resource=Resource.from_dict(data.get("resource", {})),
            log_name=data.get("logName") or data.get("log_name", ""),
            timestamp=data.get("timestamp", ""),
        )

    @property
    def project_id(self) -> str:
        """Extract project ID from log name."""
        if self.log_name.startswith("projects/"):
            parts = self.log_name.split("/")
            if len(parts) >= 2:
                return parts[1]
        return ""
