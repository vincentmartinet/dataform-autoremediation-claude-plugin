# ADR-0004: Fetch Dataform Workflow Invocation Actions for Missing Context

## Status
Accepted

## Context
When Dataform execution fails during a workflow invocation, the primary Cloud Logging entry `WorkflowInvocationCompletionLogEntry` only indicates that the workflow `terminalState` is `FAILED`. It does not contain the specific action (e.g., table or view) that failed, nor does it contain the actual BigQuery SQL error (e.g., "Syntax error", "Unrecognized name"). This omission causes the `scout_daemon.py` to skip the log as an `UNKNOWN` error, missing out on fixable LLM scenarios.

## Decision
We decided to update `scout_daemon.py` to intercept `WorkflowInvocationCompletionLogEntry` logs with a `FAILED` state. The daemon extracts the `workflowInvocationId` and queries the Dataform REST API (`:query` method on the invocation) using an authorization token from `gcloud auth print-access-token`. It then filters the returned `workflowInvocationActions` to extract the underlying action names and specific BigQuery SQL failures. These details are directly injected into the existing error handling and LLM triggering pipeline.

## Consequences
- **Positive:** Enables the plugin to autonomously fix execution-level Dataform failures that were previously invisible in the primary log payload.
- **Negative:** Adds network I/O to the daemon flow, requiring a sub-process call to `gcloud auth` and an HTTP request via `urllib.request`. The daemon must gracefully handle API timeouts or unavailable network conditions without crashing.
