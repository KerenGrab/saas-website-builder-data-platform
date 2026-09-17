import pytest

from pipeline import load_plan, loading


def _expected_counts(contract):
    counts = {}

    for dataset_number in load_plan.iter_dataset_numbers_in_load_order():
        dataset = next(
            item
            for item in contract["datasets"]
            if item["number"] == dataset_number
        )
        table_name = load_plan.get_load_spec(
            dataset_number
        )["target_table"]
        counts[table_name] = load_plan.expected_target_rows(
            dataset
        )

    return counts


def test_successful_rerun_reconciliation_accepts_expected_counts(
    canonical_contract_stub,
    monkeypatch,
):
    expected = _expected_counts(
        canonical_contract_stub
    )

    monkeypatch.setattr(
        loading,
        "inspect_target_state",
        lambda connection, target_tables=None: dict(expected),
    )

    actual = loading.reconcile_existing_target_state(
        object(),
        canonical_contract_stub,
    )

    assert actual == expected


def test_successful_rerun_reconciliation_rejects_state_drift(
    canonical_contract_stub,
    monkeypatch,
):
    drifted = _expected_counts(
        canonical_contract_stub
    )
    first_table = next(iter(drifted))
    drifted[first_table] += 1

    monkeypatch.setattr(
        loading,
        "inspect_target_state",
        lambda connection, target_tables=None: dict(drifted),
    )

    with pytest.raises(
        loading.ReconciliationError,
        match="reconciliation failed",
    ):
        loading.reconcile_existing_target_state(
            object(),
            canonical_contract_stub,
        )
