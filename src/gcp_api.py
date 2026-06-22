import json
import logging
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from typing import Any

from src.constants import GCLOUD
from src.exceptions import GCPAPIError

logger = logging.getLogger(__name__)

_token_cache: str | None = None
_token_expiry: datetime | None = None


def _get_access_token() -> str:
    global _token_cache, _token_expiry
    now = datetime.now()

    if _token_cache and _token_expiry and now < _token_expiry:
        return _token_cache

    logger.debug("Fetching new GCP access token...")
    try:
        token_proc = subprocess.run(
            [GCLOUD, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        _token_cache = token_proc.stdout.strip()
        _token_expiry = now + timedelta(minutes=45)
        return _token_cache
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch gcloud token: {e.stderr}")
        raise GCPAPIError("Failed to fetch access token") from e


def _make_request(url: str) -> dict[str, Any]:
    token = _get_access_token()
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))  # type: ignore
    except urllib.error.URLError as e:
        logger.error(f"GCP API request failed for {url}: {e}")
        raise GCPAPIError(f"API request failed: {e}") from e
    except json.JSONDecodeError as e:
        logger.error(f"GCP API returned invalid JSON for {url}")
        raise GCPAPIError("Invalid JSON from API") from e


def get_gcp_repo_url(project_id: str, location: str, repository_id: str) -> str | None:
    url = f"https://dataform.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories/{repository_id}"
    try:
        data = _make_request(url)
        repo_url = data.get("gitRemoteSettings", {}).get("url")
        if isinstance(repo_url, str):
            return repo_url
        return None
    except GCPAPIError:
        return None


def fetch_workflow_branch(
    project_id: str, location: str, repository_id: str, invocation_id: str
) -> str | None:
    url = f"https://dataform.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories/{repository_id}/workflowInvocations/{invocation_id}"
    try:
        data = _make_request(url)
        commitish = data.get("invocationConfig", {}).get("gitCommitish")
        if commitish and isinstance(commitish, str):
            return commitish

        cr_name = data.get("compilationResult")
        if cr_name and isinstance(cr_name, str):
            url_cr = f"https://dataform.googleapis.com/v1/{cr_name}"
            cr_data = _make_request(url_cr)
            cr_commitish = cr_data.get("gitCommitish")
            if cr_commitish and isinstance(cr_commitish, str):
                return cr_commitish
        return None
    except GCPAPIError:
        return None


def fetch_workflow_failed_actions(
    project_id: str, location: str, repository_id: str, invocation_id: str
) -> list[dict[str, Any]]:
    url = f"https://dataform.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories/{repository_id}/workflowInvocations/{invocation_id}:query"
    try:
        data = _make_request(url)
        failed: list[dict[str, Any]] = []
        actions = data.get("workflowInvocationActions")
        if isinstance(actions, list):
            for action in actions:
                if isinstance(action, dict) and action.get("state") == "FAILED":
                    failed.append(action)
        return failed
    except GCPAPIError:
        return []
