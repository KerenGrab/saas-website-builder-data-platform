from uuid import UUID

import pytest

from pipeline import (
    db,
    run_history,
)


class ForcedRunFailure(RuntimeError):
    pass


def _target_count(
    connection,
):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) "
            "FROM public.part9f_test_target"
        )

        return cursor.fetchone()[0]


def _start_run(
    connection,
    *,
    mode="validate",
):
    run_id = (
        run_history.new_run_id()
    )

    started_at = (
        run_history.utc_now()
    )

    run_history.create_run(
        connection,
        run_id=run_id,
        mode=mode,
        started_at=started_at,
    )

    return run_id


def test_run_ids_are_unique_uuid_values():
    first = (
        run_history.new_run_id()
    )

    second = (
        run_history.new_run_id()
    )

    assert isinstance(
        first,
        UUID,
    )

    assert isinstance(
        second,
        UUID,
    )

    assert first != second


@pytest.mark.integration
def test_success_run_history_is_persisted(
    test_db_connection,
    clean_test_state,
):
    run_id = _start_run(
        test_db_connection,
        mode="validate",
    )

    run_history.finalize_run(
        test_db_connection,

        run_id=run_id,

        status=
            run_history.STATUS_SUCCESS,

        finished_at=
            run_history.utc_now(),

        duration_ms=12,

        validation_status="PASS",

        datasets_expected=49,

        datasets_processed=49,

        raw_records_scanned=100,
    )

    row = run_history.get_run(
        test_db_connection,
        run_id,
    )

    assert (
        row["status"]
        == run_history.STATUS_SUCCESS
    )

    assert (
        row["validation_status"]
        == "PASS"
    )

    assert (
        row["datasets_processed"]
        == 49
    )

    assert (
        row["transaction_outcome"]
        is None
    )


@pytest.mark.integration
def test_failed_run_evidence_survives_business_rollback(
    test_db_connection,
    clean_test_state,
):
    run_id = _start_run(
        test_db_connection,
        mode="full-load",
    )

    def failing_work(
        connection,
    ):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO
                public.part9f_test_target
                    (id, value)
                VALUES
                    (
                        'R1',
                        'must roll back'
                    )
                """
            )

        raise ForcedRunFailure(
            "forced load failure"
        )

    with pytest.raises(
        ForcedRunFailure
    ):
        db.run_atomic(
            test_db_connection,
            failing_work,
        )

    assert (
        _target_count(
            test_db_connection
        )
        == 0
    )

    run_history.finalize_run(
        test_db_connection,

        run_id=run_id,

        status=
            run_history.STATUS_FAILED,

        finished_at=
            run_history.utc_now(),

        duration_ms=20,

        batch_id="B_FAIL",

        fingerprint="a" * 64,

        transaction_outcome=
            run_history.TRANSACTION_ROLLBACK,

        failure_stage="loading",

        error_type="ForcedRunFailure",

        error_message="forced load failure",
    )

    row = run_history.get_run(
        test_db_connection,
        run_id,
    )

    assert (
        row["status"]
        == run_history.STATUS_FAILED
    )

    assert (
        row["transaction_outcome"]
        == run_history.TRANSACTION_ROLLBACK
    )

    assert (
        row["failure_stage"]
        == "loading"
    )


@pytest.mark.integration
def test_skipped_run_has_no_target_transaction(
    test_db_connection,
    clean_test_state,
):
    run_id = _start_run(
        test_db_connection,
        mode="full-load",
    )

    run_history.finalize_run(
        test_db_connection,

        run_id=run_id,

        status=
            run_history.STATUS_SKIPPED,

        finished_at=
            run_history.utc_now(),

        duration_ms=3,

        batch_id="B_SKIP",

        fingerprint="b" * 64,

        transaction_outcome=None,
    )

    row = run_history.get_run(
        test_db_connection,
        run_id,
    )

    assert (
        row["status"]
        == run_history.STATUS_SKIPPED
    )

    assert (
        row["transaction_outcome"]
        is None
    )


@pytest.mark.integration
def test_conflict_failure_records_no_target_transaction(
    test_db_connection,
    clean_test_state,
):
    run_id = _start_run(
        test_db_connection,
        mode="full-load",
    )

    run_history.finalize_run(
        test_db_connection,

        run_id=run_id,

        status=
            run_history.STATUS_FAILED,

        finished_at=
            run_history.utc_now(),

        duration_ms=4,

        batch_id="B_CONFLICT",

        fingerprint="c" * 64,

        transaction_outcome=None,

        failure_stage="rerun_check",

        error_type="BatchIdentityConflictError",

        error_message=(
            "same batch id, "
            "different content"
        ),
    )

    row = run_history.get_run(
        test_db_connection,
        run_id,
    )

    assert (
        row["status"]
        == run_history.STATUS_FAILED
    )

    assert (
        row["failure_stage"]
        == "rerun_check"
    )

    assert (
        row["error_type"]
        == "BatchIdentityConflictError"
    )

    assert (
        row["transaction_outcome"]
        is None
    )


@pytest.mark.integration
def test_dq_fail_is_successful_execution_with_dq_fail_outcome(
    test_db_connection,
    clean_test_state,
):
    run_id = _start_run(
        test_db_connection,
        mode="dq",
    )

    run_history.finalize_run(
        test_db_connection,

        run_id=run_id,

        status=
            run_history.STATUS_SUCCESS,

        finished_at=
            run_history.utc_now(),

        duration_ms=8,

        dq_rules_executed=32,

        dq_pass_count=31,

        dq_fail_count=1,

        dq_total_violations=2,

        dq_status="FAIL",

        transaction_outcome=None,
    )

    row = run_history.get_run(
        test_db_connection,
        run_id,
    )

    assert (
        row["status"]
        == run_history.STATUS_SUCCESS
    )

    assert (
        row["dq_status"]
        == "FAIL"
    )

    assert (
        row["dq_fail_count"]
        == 1
    )

    assert (
        row["transaction_outcome"]
        is None
    )