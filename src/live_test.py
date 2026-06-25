"""Module for executing live tests on Dataform actions via BigQuery."""

import json
import logging
import subprocess
import uuid

logger = logging.getLogger(__name__)


def run_live_test(action_name: str, wt_path: str) -> bool:  # noqa: C901
    """Runs a dry-run live test for the specified action using a temporary dataset.

    Args:
        action_name: The name of the Dataform action to test.
        wt_path: The working tree directory path containing the Dataform project.

    Returns:
        bool: True if the live test passes, False otherwise.
    """
    if not action_name:
        logger.info("No specific action provided; skipping live test.")
        return True

    # 1. Compile the project to JSON to extract dependencies
    compile_cmd = ["dataform", "compile", "--json"]
    compile_res = subprocess.run(
        compile_cmd, cwd=wt_path, capture_output=True, text=True
    )

    if compile_res.returncode != 0:
        logger.error(f"Compilation failed before live test:\n{compile_res.stderr}")
        return False

    try:
        compiled = json.loads(compile_res.stdout)
    except json.JSONDecodeError:
        logger.error("Failed to parse Dataform compile JSON output.")
        return False

    project_config = compiled.get("projectConfig") or {}
    default_database = project_config.get("defaultDatabase", "")
    default_schema = project_config.get("defaultSchema", "")

    if not default_database or not default_schema:
        logger.warning(
            "defaultDatabase or defaultSchema not found in projectConfig. "
            "Skipping live test."
        )
        return True

    # Find the dependencies for the action
    actions = (
        (compiled.get("tables") or [])
        + (compiled.get("operations") or [])
        + (compiled.get("assertions") or [])
    )

    deps_to_replicate = []
    for action in actions:
        target = action.get("target") or {}
        if target.get("name") == action_name:
            for dep in action.get("dependencyTargets") or []:
                if (
                    dep.get("database") == default_database
                    and dep.get("schema") == default_schema
                    and dep.get("name") != action_name
                ):
                    deps_to_replicate.append(dep.get("name"))
            break
    else:
        logger.warning(
            f"Action '{action_name}' not found in compiled project. Skipping live test."
        )
        return True

    temp_dataset = f"scout_tmp_{uuid.uuid4().hex[:8]}"
    logger.info(f"Setting up live test in temporary dataset: {temp_dataset}")

    try:
        # Create temporary dataset
        mk_cmd = ["bq", "mk", "-f", "-d", f"{default_database}:{temp_dataset}"]
        subprocess.run(mk_cmd, check=True, capture_output=True, text=True)

        # Replicate schema of dependencies
        for dep_name in deps_to_replicate:
            # We use BigQuery CREATE TABLE ... AS SELECT ... LIMIT 0 to copy the schema.
            # This works for copying views as tables as well.
            query = (
                f"CREATE TABLE `{default_database}.{temp_dataset}.{dep_name}` "
                f"AS SELECT * FROM `{default_database}.{default_schema}.{dep_name}` "
                "LIMIT 0"
            )
            bq_query_cmd = ["bq", "query", "--use_legacy_sql=false", query]
            bq_res = subprocess.run(bq_query_cmd, capture_output=True, text=True)
            if bq_res.returncode != 0:
                logger.warning(
                    f"Failed to replicate dependency {dep_name}: {bq_res.stderr}"
                )

        # Run Dataform dry-run
        run_cmd = [
            "dataform",
            "run",
            "--actions",
            action_name,
            "--default-database",
            default_database,
            "--default-schema",
            temp_dataset,
            "--dry-run",
        ]
        run_res = subprocess.run(run_cmd, cwd=wt_path, capture_output=True, text=True)

        if run_res.returncode == 0:
            logger.info(f"Live test for '{action_name}' passed successfully.")
            return True
        else:
            logger.error(f"Live test dry-run failed:\n{run_res.stderr}")
            return False

    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing bq commands during live test: {e.stderr}")
        return False
    finally:
        # Cleanup temporary dataset
        logger.info(f"Cleaning up temporary dataset: {temp_dataset}")
        rm_cmd = ["bq", "rm", "-r", "-f", "-d", f"{default_database}:{temp_dataset}"]
        subprocess.run(rm_cmd, capture_output=True, text=True)
