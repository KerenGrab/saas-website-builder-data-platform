import hashlib
import os

import pytest

from pipeline import load_plan


@pytest.fixture
def canonical_contract_stub():
    """Small metadata-only 49-dataset contract with canonical total counts."""
    datasets = []

    for dataset_number in range(1, 50):
        spec = load_plan.get_load_spec(dataset_number)
        duplicate_count = spec["expected_exact_duplicates"]
        rows = max(1, duplicate_count + 1)

        datasets.append(
            {
                "number": dataset_number,
                "dataset": spec["source_dataset"],
                "format": (
                    "jsonl"
                    if spec["deduplicate_by_event_id"]
                    else "csv"
                ),
                "rows": rows,
                "sha256": hashlib.sha256(
                    f"dataset-{dataset_number}".encode("utf-8")
                ).hexdigest(),
            }
        )

    current_total = sum(
        dataset["rows"]
        for dataset in datasets
    )

    datasets[0]["rows"] += (
        load_plan.EXPECTED_REFERENCE_RAW_ROWS
        - current_total
    )

    return {
        "contract_version": "test-1.0",
        "status": "FROZEN",
        "datasets_expected": 49,
        "datasets_generated": 49,
        "dataset_count": 49,
        "datasets": datasets,
    }


@pytest.fixture(scope="session")
def test_db_connection():
    """Open only the explicitly named isolated PostgreSQL test database."""
    if os.getenv("RUN_DB_TESTS", "").strip().lower() not in {
        "1",
        "true",
        "yes",
    }:
        pytest.skip(
            "Integration tests disabled. "
            "Set RUN_DB_TESTS=1 after creating the test DB."
        )

    test_db_name = os.getenv("TEST_DB_NAME", "").strip()

    if not test_db_name:
        pytest.fail(
            "TEST_DB_NAME must be configured before integration tests can run."
        )

    blocked_names = {
        "saas_website_builder",
        "saas_website_builder_9d",
        os.getenv(
            "CANONICAL_DB_NAME",
            "saas_website_builder_9d",
        ).strip(),
    }

    if (
        test_db_name in blocked_names
        or not test_db_name.endswith("_test")
    ):
        pytest.fail(
            "Unsafe TEST_DB_NAME. Integration tests require a separate database "
            "whose name ends with '_test' and is not a canonical database."
        )

    import psycopg

    from pipeline import config

    if not config.DB_USER or not config.DB_PASSWORD:
        pytest.fail(
            "DB_USER and DB_PASSWORD must be configured for integration tests."
        )

    connection = psycopg.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=test_db_name,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        connect_timeout=5,
        autocommit=True,
    )

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT current_database()"
        )

        actual_db_name = (
            cursor.fetchone()[0]
        )

    if (
        actual_db_name != test_db_name
        or not actual_db_name.endswith("_test")
    ):
        connection.close()

        pytest.fail(
            "Test database safety guard failed before any test writes."
        )

    yield connection

    connection.close()


@pytest.fixture
def clean_test_state(
    test_db_connection,
):
    """Create tiny test-only tables and return them to a clean state."""
    from pipeline import (
        rerun,
        run_history,
    )

    with test_db_connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.part9f_test_parent (
                id TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.part9f_test_child (
                id TEXT PRIMARY KEY,
                parent_id TEXT NOT NULL
                    REFERENCES public.part9f_test_parent(id),
                value TEXT NOT NULL
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS public.part9f_test_target (
                id TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

    rerun.ensure_batch_state_table(
        test_db_connection
    )

    run_history.ensure_run_history_table(
        test_db_connection
    )

    def clean():
        with test_db_connection.cursor() as cursor:
            cursor.execute(
                "TRUNCATE TABLE "
                "public.part9f_test_child, "
                "public.part9f_test_parent, "
                "public.part9f_test_target"
            )

            cursor.execute(
                "DELETE FROM pipeline_meta.run_history"
            )

            cursor.execute(
                "DELETE FROM pipeline_meta.batch_state"
            )

    clean()

    yield

    clean()