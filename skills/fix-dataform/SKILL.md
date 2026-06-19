---
description: Analyze and fix a failing Dataform .sqlx file based on a GCP error log entry. Use when the dataform-scout daemon detects a Dataform compilation or execution error, or when asked to fix a Dataform SQL error.
---

# Skill: fix-dataform

You have been triggered by the `dataform-scout` daemon because a Dataform compilation or execution error was detected in Google Cloud Logging.

## Context provided in the prompt

- **File**: the `.sqlx` file path that contains the failing SQL definition (may be absent if the log did not reference one explicitly).
- **Error**: the raw error message extracted from the GCP log entry.
- **Branch**: the local git branch that was already created for this fix (`fix/dataform-<timestamp>`).

## Your task

1. **Read the failing file.** If a `File:` path was provided, read its full contents. If the path is relative, resolve it from the repository root.

2. **Analyse the error.** Common BigQuery/Dataform issues include:
   - Unresolved `ref()` or `resolve()` calls pointing to non-existent targets.
   - Invalid SQL syntax (missing commas, unclosed parentheses, reserved-word conflicts).
   - Type mismatches in schema declarations.
   - Incorrect `config { … }` block syntax.

3. **Apply a minimal fix.** Edit only the lines required to resolve the reported error. Do not refactor unrelated code.

4. **Verify with `dataform compile`.** Run the following command from the repository root:
   ```
   dataform compile
   ```
   - If it exits with code 0, the fix is valid — proceed.
   - If it still reports errors, iterate on the fix until `dataform compile` succeeds.

5. **Present the diff and ask for confirmation.** Show the user a `git diff` of the changed file and explicitly ask: _"Does this fix look correct? Confirm to keep it, or type 'revert' to undo."_

6. **On confirmation:** do nothing further — leave the branch and changes in place for the developer to review and open a PR manually.

7. **On revert:** run `git checkout -- <file>` to restore the original and inform the user.

## Hard constraints

- **Never** run `git push` or `git push --force` under any circumstances.
- **Never** modify files outside the repository root.
- Only edit the specific `.sqlx` file(s) implicated by the error.
