"""Persistent run-history storage for Part 9G operational evidence."""

from datetime import datetime, timezone
from uuid import uuid4

from psycopg import sql


PIPELINE_META_SCHEMA = "pipeline_meta"
RUN_HISTORY_TABLE = "run_history"

STATUS_RUNNING = "RUNNING"
STATUS_SUCCESS = "SUCCESS"
STATUS_FAILED = "FAILED"
STATUS_SKIPPED = "SKIPPED"

TRANSACTION_COMMIT = "COMMIT"
TRANSACTION_ROLLBACK = "ROLLBACK"


REQUIRED_COLUMNS = {
    "run_id",
    "batch_id",
    "fingerprint",
    "mode",
    "status",
    "started_at",
    "finished_at",
    "duration_ms",
    "validation_status",
    "datasets_expected",
    "datasets_processed",
    "raw_records_scanned",
    "duplicates_skipped",
    "rows_loaded",
    "target_tables_reconciled",
    "transaction_outcome",
    "dq_rules_executed",
    "dq_pass_count",
    "dq_fail_count",
    "dq_total_violations",
    "dq_status",
    "failure_stage",
    "error_type",
    "error_message",
}


def utc_now():
    return datetime.now(timezone.utc)


def new_run_id():
    return uuid4()


def ensure_run_history_table(connection):
    """Create 9G operational metadata objects and verify the expected shape."""

    if not connection.autocommit:
        raise RuntimeError(
            "Run-history setup requires a connection "
            "opened with autocommit=True."
        )

    create_schema = sql.SQL(
        "CREATE SCHEMA IF NOT EXISTS {}"
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA)
    )

    create_table = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {}.{} (
            run_id UUID PRIMARY KEY,

            batch_id TEXT NULL,
            fingerprint CHAR(64) NULL,

            mode TEXT NOT NULL,

            status TEXT NOT NULL
                CHECK (
                    status IN (
                        'RUNNING',
                        'SUCCESS',
                        'FAILED',
                        'SKIPPED'
                    )
                ),

            started_at TIMESTAMPTZ NOT NULL,
            finished_at TIMESTAMPTZ NULL,

            duration_ms BIGINT NULL
                CHECK (
                    duration_ms IS NULL
                    OR duration_ms >= 0
                ),

            validation_status TEXT NULL
                CHECK (
                    validation_status IS NULL
                    OR validation_status IN ('PASS', 'FAIL')
                ),

            datasets_expected INTEGER NULL
                CHECK (
                    datasets_expected IS NULL
                    OR datasets_expected >= 0
                ),

            datasets_processed INTEGER NULL
                CHECK (
                    datasets_processed IS NULL
                    OR datasets_processed >= 0
                ),

            raw_records_scanned BIGINT NULL
                CHECK (
                    raw_records_scanned IS NULL
                    OR raw_records_scanned >= 0
                ),

            duplicates_skipped BIGINT NULL
                CHECK (
                    duplicates_skipped IS NULL
                    OR duplicates_skipped >= 0
                ),

            rows_loaded BIGINT NULL
                CHECK (
                    rows_loaded IS NULL
                    OR rows_loaded >= 0
                ),

            target_tables_reconciled INTEGER NULL
                CHECK (
                    target_tables_reconciled IS NULL
                    OR target_tables_reconciled >= 0
                ),

            transaction_outcome TEXT NULL
                CHECK (
                    transaction_outcome IS NULL
                    OR transaction_outcome IN (
                        'COMMIT',
                        'ROLLBACK'
                    )
                ),

            dq_rules_executed INTEGER NULL
                CHECK (
                    dq_rules_executed IS NULL
                    OR dq_rules_executed >= 0
                ),

            dq_pass_count INTEGER NULL
                CHECK (
                    dq_pass_count IS NULL
                    OR dq_pass_count >= 0
                ),

            dq_fail_count INTEGER NULL
                CHECK (
                    dq_fail_count IS NULL
                    OR dq_fail_count >= 0
                ),

            dq_total_violations BIGINT NULL
                CHECK (
                    dq_total_violations IS NULL
                    OR dq_total_violations >= 0
                ),

            dq_status TEXT NULL
                CHECK (
                    dq_status IS NULL
                    OR dq_status IN ('PASS', 'FAIL')
                ),

            failure_stage TEXT NULL,
            error_type TEXT NULL,
            error_message TEXT NULL
        )
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(RUN_HISTORY_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(create_schema)
        cursor.execute(create_table)

    _validate_run_history_columns(connection)


def _validate_run_history_columns(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s
              AND table_name = %s
            """,
            (
                PIPELINE_META_SCHEMA,
                RUN_HISTORY_TABLE,
            ),
        )

        actual_columns = {
            row[0]
            for row in cursor.fetchall()
        }

    missing = sorted(
        REQUIRED_COLUMNS - actual_columns
    )

    if missing:
        raise RuntimeError(
            "Existing pipeline_meta.run_history "
            "schema is incompatible. "
            f"Missing columns: {missing}"
        )


def create_run(
    connection,
    *,
    run_id,
    mode,
    started_at,
):
    """Persist the initial RUNNING row before executing pipeline work."""

    query = sql.SQL(
        """
        INSERT INTO {}.{}
            (
                run_id,
                mode,
                status,
                started_at
            )
        VALUES (%s, %s, %s, %s)
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(RUN_HISTORY_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                run_id,
                mode,
                STATUS_RUNNING,
                started_at,
            ),
        )


def finalize_run(
    connection,
    *,
    run_id,
    status,
    finished_at,
    duration_ms,
    batch_id=None,
    fingerprint=None,
    validation_status=None,
    datasets_expected=None,
    datasets_processed=None,
    raw_records_scanned=None,
    duplicates_skipped=None,
    rows_loaded=None,
    target_tables_reconciled=None,
    transaction_outcome=None,
    dq_rules_executed=None,
    dq_pass_count=None,
    dq_fail_count=None,
    dq_total_violations=None,
    dq_status=None,
    failure_stage=None,
    error_type=None,
    error_message=None,
):
    """Finalize one RUNNING row with its durable execution evidence."""

    query = sql.SQL(
        """
        UPDATE {}.{}
        SET
            batch_id = %s,
            fingerprint = %s,
            status = %s,
            finished_at = %s,
            duration_ms = %s,

            validation_status = %s,

            datasets_expected = %s,
            datasets_processed = %s,
            raw_records_scanned = %s,

            duplicates_skipped = %s,
            rows_loaded = %s,
            target_tables_reconciled = %s,

            transaction_outcome = %s,

            dq_rules_executed = %s,
            dq_pass_count = %s,
            dq_fail_count = %s,
            dq_total_violations = %s,
            dq_status = %s,

            failure_stage = %s,
            error_type = %s,
            error_message = %s

        WHERE run_id = %s
          AND status = %s
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(RUN_HISTORY_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                batch_id,
                fingerprint,
                status,
                finished_at,
                duration_ms,

                validation_status,

                datasets_expected,
                datasets_processed,
                raw_records_scanned,

                duplicates_skipped,
                rows_loaded,
                target_tables_reconciled,

                transaction_outcome,

                dq_rules_executed,
                dq_pass_count,
                dq_fail_count,
                dq_total_violations,
                dq_status,

                failure_stage,
                error_type,
                error_message,

                run_id,
                STATUS_RUNNING,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Could not finalize exactly one "
                "RUNNING run-history row."
            )


def get_run(
    connection,
    run_id,
):
    query = sql.SQL(
        """
        SELECT
            run_id,
            batch_id,
            fingerprint,
            mode,
            status,
            started_at,
            finished_at,
            duration_ms,
            validation_status,
            datasets_expected,
            datasets_processed,
            raw_records_scanned,
            duplicates_skipped,
            rows_loaded,
            target_tables_reconciled,
            transaction_outcome,
            dq_rules_executed,
            dq_pass_count,
            dq_fail_count,
            dq_total_violations,
            dq_status,
            failure_stage,
            error_type,
            error_message
        FROM {}.{}
        WHERE run_id = %s
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(RUN_HISTORY_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (run_id,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        columns = [
            column.name
            for column in cursor.description
        ]

    result = dict(
        zip(
            columns,
            row,
        )
    )

    if result["fingerprint"] is not None:
        result["fingerprint"] = str(
            result["fingerprint"]
        ).strip()

    return result