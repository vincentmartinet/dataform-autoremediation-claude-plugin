class ScoutError(Exception):
    """Base class for all Scout-specific exceptions."""

    pass


class GCPAPIError(ScoutError):
    """Raised when an interaction with the GCP API fails."""

    pass


class GitOpsError(ScoutError):
    """Raised when a Git operation fails."""

    pass


class MissingDependencyError(ScoutError):
    """Raised when required executables are missing."""

    pass
