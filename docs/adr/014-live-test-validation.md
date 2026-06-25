# 14. Live Test Validation via BigQuery

Date: 2026-06-25

## Status

Accepted

## Context

While `dataform compile` ensures the SQLX syntax is valid and dependencies can be resolved, it does not validate against the actual underlying BigQuery data schema. Queries with missing columns, type mismatches, or non-existent tables will pass compilation but fail during the actual pipeline run.
We needed a way to perform a "live test" to simulate the fix directly against BigQuery, matching the functionality available in the deployed (cloud) version of the agent. Since the local daemon must remain zero-dependency (no `google-cloud-bigquery` library allowed), we needed to execute this through existing CLI tools.

## Decision

We will implement a "live test" using the `bq` and `dataform` CLIs directly:
1. Parse the `dataform compile --json` output to find direct dependencies of the fixed action.
2. Generate a temporary dataset name.
3. Use `bq mk` to create the temporary dataset.
4. Replicate the schema of each dependency using `bq query --use_legacy_sql=false "CREATE TABLE <temp_dataset>.<dep> AS SELECT * FROM <source> LIMIT 0"`.
5. Run `dataform run --dry-run --actions <action> --default-schema <temp_dataset>` to validate the logic against BigQuery without incurring significant costs.
6. Clean up the temporary dataset using `bq rm`.

## Consequences

- The automated fix loop now accurately catches missing columns or table schema errors before proposing the PR.
- The daemon remains zero-dependency since we utilize subprocess calls to `bq` and `dataform`.
- Testing adds a slight delay and requires sufficient `gcloud` permissions to create/delete datasets and run dry-run queries.
