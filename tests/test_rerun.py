from copy import deepcopy

import pytest

from pipeline import loading, rerun


class ForcedBatchFailure(RuntimeError):
    pass


def _target_count(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT COUNT(*) FROM public.part9f_test_target"
        )
        return cursor.fetchone()[0]



def test_default_batch_id_is_stable_from_contract_version(canonical_contract_stub):
    assert rerun.resolve_batch_id(
        canonical_contract_stub
    ) == "canonical-contract-vtest-1.0"


def test_explicit_batch_id_overrides_default(canonical_contract_stub):
    assert rerun.resolve_batch_id(
        canonical_contract_stub,
        "BATCH_2026_08_29",
    ) == "BATCH_2026_08_29"

def test_batch_fingerprint_is_deterministic(canonical_contract_stub):
    first = rerun.calculate_batch_fingerprint(
        canonical_contract_stub
    )
    second = rerun.calculate_batch_fingerprint(
        deepcopy(canonical_contract_stub)
    )

    assert first == second
    assert len(first) == 64


def test_changed_content_changes_batch_fingerprint(canonical_contract_stub):
    changed = deepcopy(
        canonical_contract_stub
    )
    changed["datasets"][0]["sha256"] = "f" * 64

    assert rerun.calculate_batch_fingerprint(
        canonical_contract_stub
    ) != rerun.calculate_batch_fingerprint(
        changed
    )


def test_failed_same_batch_is_retryable():
    state = {
        "batch_id": "B1",
        "fingerprint": "a" * 64,
        "status": rerun.STATUS_FAILED,
        "attempt_count": 1,
    }

    assert rerun.decide_batch_action(
        state,
        "a" * 64,
    ) == rerun.ACTION_PROCESS


def test_successful_same_batch_is_skipped():
    state = {
        "batch_id": "B1",
        "fingerprint": "a" * 64,
        "status": rerun.STATUS_SUCCESS,
        "attempt_count": 1,
    }

    assert rerun.decide_batch_action(
        state,
        "a" * 64,
    ) == rerun.ACTION_SKIP


def test_same_batch_with_different_fingerprint_is_rejected():
    state = {
        "batch_id": "B1",
        "fingerprint": "a" * 64,
        "status": rerun.STATUS_SUCCESS,
        "attempt_count": 1,
    }

    with pytest.raises(rerun.BatchIdentityConflictError):
        rerun.decide_batch_action(
            state,
            "b" * 64,
        )


def test_processing_same_batch_is_rejected_as_in_progress():
    state = {
        "batch_id": "B1",
        "fingerprint": "a" * 64,
        "status": rerun.STATUS_PROCESSING,
        "attempt_count": 1,
    }

    with pytest.raises(rerun.BatchInProgressError):
        rerun.decide_batch_action(
            state,
            "a" * 64,
        )


@pytest.mark.integration
def test_retry_after_failed_batch_succeeds_once(
    test_db_connection,
    clean_test_state,
):
    batch_id = "B_RETRY"
    fingerprint = "a" * 64

    def failing_work(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.part9f_test_target (id, value)
                VALUES ('R1', 'first attempt')
                """
            )
        raise ForcedBatchFailure("forced batch failure")

    with pytest.raises(ForcedBatchFailure):
        rerun.execute_rerun_aware_batch(
            connection=test_db_connection,
            batch_id=batch_id,
            fingerprint=fingerprint,
            pre_write_check=lambda connection: (
                loading.assert_target_is_empty(
                    connection,
                    target_tables=("part9f_test_target",),
                )
            ),
            work=failing_work,
        )

    assert _target_count(test_db_connection) == 0
    failed_state = rerun.get_batch_state(
        test_db_connection,
        batch_id,
    )
    assert failed_state["status"] == rerun.STATUS_FAILED
    assert failed_state["attempt_count"] == 1

    def successful_work(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.part9f_test_target (id, value)
                VALUES ('R1', 'retry success')
                """
            )
        return "loaded"

    outcome = rerun.execute_rerun_aware_batch(
        connection=test_db_connection,
        batch_id=batch_id,
        fingerprint=fingerprint,
        pre_write_check=lambda connection: (
            loading.assert_target_is_empty(
                connection,
                target_tables=("part9f_test_target",),
            )
        ),
        work=successful_work,
    )

    assert outcome["action"] == rerun.ACTION_PROCESS
    assert outcome["result"] == "loaded"
    assert _target_count(test_db_connection) == 1

    success_state = rerun.get_batch_state(
        test_db_connection,
        batch_id,
    )
    assert success_state["status"] == rerun.STATUS_SUCCESS
    assert success_state["attempt_count"] == 2


@pytest.mark.integration
def test_same_successful_batch_is_idempotent_against_real_state(
    test_db_connection,
    clean_test_state,
):
    batch_id = "B_IDEMPOTENT"
    fingerprint = "c" * 64
    work_call_count = {"value": 0}

    def work(connection):
        work_call_count["value"] += 1
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.part9f_test_target (id, value)
                VALUES ('I1', 'loaded once')
                """
            )
        return "loaded"

    first = rerun.execute_rerun_aware_batch(
        connection=test_db_connection,
        batch_id=batch_id,
        fingerprint=fingerprint,
        pre_write_check=lambda connection: (
            loading.assert_target_is_empty(
                connection,
                target_tables=("part9f_test_target",),
            )
        ),
        verify_existing_state=lambda connection: (
            None
            if _target_count(connection) == 1
            else (_ for _ in ()).throw(
                AssertionError("existing state drifted")
            )
        ),
        work=work,
    )

    before = _target_count(
        test_db_connection
    )

    second = rerun.execute_rerun_aware_batch(
        connection=test_db_connection,
        batch_id=batch_id,
        fingerprint=fingerprint,
        pre_write_check=lambda connection: (
            loading.assert_target_is_empty(
                connection,
                target_tables=("part9f_test_target",),
            )
        ),
        verify_existing_state=lambda connection: (
            None
            if _target_count(connection) == 1
            else (_ for _ in ()).throw(
                AssertionError("existing state drifted")
            )
        ),
        work=work,
    )

    after = _target_count(
        test_db_connection
    )

    assert first["action"] == rerun.ACTION_PROCESS
    assert second["action"] == rerun.ACTION_SKIP
    assert before == 1
    assert after == before
    assert work_call_count["value"] == 1


@pytest.mark.integration
def test_fingerprint_conflict_is_rejected_before_target_mutation(
    test_db_connection,
    clean_test_state,
):
    batch_id = "B_CONFLICT"

    def work(connection):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO public.part9f_test_target (id, value)
                VALUES ('C1', 'original')
                """
            )
        return "loaded"

    rerun.execute_rerun_aware_batch(
        connection=test_db_connection,
        batch_id=batch_id,
        fingerprint="d" * 64,
        pre_write_check=lambda connection: (
            loading.assert_target_is_empty(
                connection,
                target_tables=("part9f_test_target",),
            )
        ),
        work=work,
    )

    before = _target_count(
        test_db_connection
    )

    with pytest.raises(rerun.BatchIdentityConflictError):
        rerun.execute_rerun_aware_batch(
            connection=test_db_connection,
            batch_id=batch_id,
            fingerprint="e" * 64,
            pre_write_check=lambda connection: (
                loading.assert_target_is_empty(
                    connection,
                    target_tables=("part9f_test_target",),
                )
            ),
            work=lambda connection: (_ for _ in ()).throw(
                AssertionError("conflicting work must never run")
            ),
        )

    after = _target_count(
        test_db_connection
    )

    assert before == 1
    assert after == before
