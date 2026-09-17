-- Canonical pipeline operational metadata.
-- Source of truth:
--   pipeline/rerun.py
--   pipeline/run_history.py

CREATE SCHEMA IF NOT EXISTS pipeline_meta;


CREATE TABLE IF NOT EXISTS pipeline_meta.batch_state (
    batch_id TEXT PRIMARY KEY,
    fingerprint CHAR(64) NOT NULL,

    status TEXT NOT NULL
        CHECK (
            status IN (
                'PROCESSING',
                'FAILED',
                'SUCCESS'
            )
        ),

    attempt_count INTEGER NOT NULL
        CHECK (attempt_count >= 1)
);


CREATE TABLE IF NOT EXISTS pipeline_meta.run_history (
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
);
