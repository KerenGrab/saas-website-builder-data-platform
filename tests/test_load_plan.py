import pytest

from pipeline import load_plan


def test_canonical_load_plan_covers_all_49_datasets(canonical_contract_stub):
    summary = load_plan.validate_load_plan(
        canonical_contract_stub
    )

    assert summary["datasets"] == 49
    assert summary["execution_groups"] == 5
    assert summary["projection_cases"] == 2
    assert summary["duplicate_aware_streams"] == 5
    assert summary["raw_rows"] == load_plan.EXPECTED_REFERENCE_RAW_ROWS
    assert (
        summary["expected_target_rows"]
        == load_plan.EXPECTED_REFERENCE_TARGET_ROWS
    )


def test_missing_load_mapping_is_rejected(canonical_contract_stub, monkeypatch):
    monkeypatch.delitem(
        load_plan.CANONICAL_DATASETS,
        49,
    )

    with pytest.raises(ValueError, match="cover Datasets #1-#49"):
        load_plan.validate_load_plan(
            canonical_contract_stub
        )


def test_projection_and_duplicate_metadata_match_canonical_cases():
    assert load_plan.get_load_spec(8)["drop_fields"] == (
        "user_id",
        "account_id",
    )
    assert load_plan.get_load_spec(36)["drop_fields"] == (
        "website_id",
    )
    assert set(load_plan.EXPECTED_EXACT_DUPLICATES) == {
        31,
        34,
        38,
        40,
        42,
    }
