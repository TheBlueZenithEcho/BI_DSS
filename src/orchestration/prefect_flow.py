
"""Prefect flow for the Hotel Analytics Pipeline."""

import os
from pathlib import Path

from prefect import flow, task
from prefect_shell import ShellOperation

# Load environment variables
import src.common  # noqa: F401


# ============================================================
# PATH CONFIGURATION
# ============================================================

# prefect_flow.py nằm trong src/orchestration/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DBT_PROJECT_DIR = PROJECT_ROOT / "dbt" / "hotel_dwh"

# Use DBT_PROFILES_DIR if configured; otherwise use ~/.dbt
PROFILES_DIR = Path(
    os.getenv("DBT_PROFILES_DIR") or (Path.home() / ".dbt")
).expanduser().resolve()


# ============================================================
# VALIDATE PATHS
# ============================================================

def validate_dbt_paths():
    if not DBT_PROJECT_DIR.exists():
        raise FileNotFoundError(
            f"dbt project directory not found: {DBT_PROJECT_DIR}"
        )

    if not (DBT_PROJECT_DIR / "dbt_project.yml").exists():
        raise FileNotFoundError(
            f"dbt_project.yml not found in: {DBT_PROJECT_DIR}"
        )

    if not PROFILES_DIR.exists():
        raise FileNotFoundError(
            f"dbt profiles directory not found: {PROFILES_DIR}"
        )

    if not (PROFILES_DIR / "profiles.yml").exists():
        raise FileNotFoundError(
            f"profiles.yml not found in: {PROFILES_DIR}"
        )


# ============================================================
# BRONZE: INGESTION
# ============================================================

@task(name="ingest-bronze")
def ingest_bronze():
    from src.ingestion import snowflake_ingest

    return snowflake_ingest.ingest_bronze_to_snowflake()


# ============================================================
# SILVER / GOLD: DBT EXECUTION
# ============================================================

@task(name="run-dbt")
def run_dbt(layer: str):
    validate_dbt_paths()

    if layer not in ["silver", "gold"]:
        raise ValueError(f"Invalid dbt layer: {layer}")

    selector = f"path:models/{layer}"

    dbt_cmd = (
        f'dbt run '
        f'--profiles-dir "{PROFILES_DIR}" '
        f'--project-dir "{DBT_PROJECT_DIR}" '
        f'--select {selector}'
    )

    print(f"Executing: {dbt_cmd}")

    return ShellOperation(
        commands=[dbt_cmd]
    ).run()


# ============================================================
# DBT TEST
# ============================================================

@task(name="run-dbt-test")
def run_dbt_test():
    validate_dbt_paths()

    test_cmd = (
        f'dbt test '
        f'--profiles-dir "{PROFILES_DIR}" '
        f'--project-dir "{DBT_PROJECT_DIR}"'
    )

    print(f"Executing: {test_cmd}")

    return ShellOperation(
        commands=[test_cmd]
    ).run()


# ============================================================
# MAIN PIPELINE
# ============================================================

@flow(
    name="hotel-analytics-pipeline",
    log_prints=True
)
def hotel_analytics_pipeline():

    print("=" * 60)
    print("HOTEL ANALYTICS PIPELINE")
    print("=" * 60)

    print(f"Project root : {PROJECT_ROOT}")
    print(f"dbt project  : {DBT_PROJECT_DIR}")
    print(f"dbt profiles : {PROFILES_DIR}")

    # Step 1: Bronze
    print("\n[1/4] Running Bronze ingestion...")

    ingest_result = ingest_bronze()

    if not ingest_result or not ingest_result.get("success"):
        raise RuntimeError("Bronze ingestion failed!")

    print("Bronze ingestion completed.")

    # Step 2: Silver
    print("\n[2/4] Running Silver models...")

    run_dbt(layer="silver")

    print("Silver transformation completed.")

    # Step 3: Gold
    print("\n[3/4] Running Gold models...")

    run_dbt(layer="gold")

    print("Gold transformation completed.")

    # Step 4: Tests
    print("\n[4/4] Running dbt tests...")

    run_dbt_test()

    print("\n" + "=" * 60)
    print("HOTEL ANALYTICS PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 60)


if __name__ == "__main__":
    hotel_analytics_pipeline()
