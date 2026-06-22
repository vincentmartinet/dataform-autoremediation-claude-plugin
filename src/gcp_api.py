import json
import subprocess
import sys
import urllib.request
from constants import GCLOUD


def get_gcp_repo_url(project_id: str, location: str, repository_id: str) -> str | None:
    try:
        token_proc = subprocess.run(
            [GCLOUD, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        token = token_proc.stdout.strip()
        url = f"https://dataform.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories/{repository_id}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        return data.get("gitRemoteSettings", {}).get("url")
    except Exception as e:
        print(f"[scout] Failed to fetch repo url: {e}", file=sys.stderr)
    return None


def fetch_workflow_branch(
    project_id: str, location: str, repository_id: str, invocation_id: str
) -> str | None:
    try:
        token_proc = subprocess.run(
            [GCLOUD, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        token = token_proc.stdout.strip()
        url = f"https://dataform.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories/{repository_id}/workflowInvocations/{invocation_id}"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        commitish = data.get("invocationConfig", {}).get("gitCommitish")
        if commitish:
            return commitish

        cr_name = data.get("compilationResult")
        if cr_name:
            url_cr = f"https://dataform.googleapis.com/v1/{cr_name}"
            req_cr = urllib.request.Request(url_cr)
            req_cr.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req_cr) as response_cr:
                cr_data = json.loads(response_cr.read().decode("utf-8"))
                return cr_data.get("gitCommitish")
    except Exception as e:
        print(f"[scout] Failed to fetch workflow branch: {e}", file=sys.stderr)
    return None


def fetch_workflow_failed_actions(
    project_id: str, location: str, repository_id: str, invocation_id: str
) -> list[dict]:
    try:
        token_proc = subprocess.run(
            [GCLOUD, "auth", "print-access-token"],
            capture_output=True,
            text=True,
            check=True,
        )
        token = token_proc.stdout.strip()
        url = f"https://dataform.googleapis.com/v1/projects/{project_id}/locations/{location}/repositories/{repository_id}/workflowInvocations/{invocation_id}:query"
        req = urllib.request.Request(url)
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))

        failed = []
        for action in data.get("workflowInvocationActions", []):
            if action.get("state") == "FAILED":
                failed.append(action)
        return failed
    except Exception as e:
        print(f"[scout] Failed to fetch workflow actions: {e}", file=sys.stderr)
        return []
