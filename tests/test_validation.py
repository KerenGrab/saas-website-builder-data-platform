import pytest

from pipeline import validation


def test_missing_required_field_is_rejected():
    dataset = {
        "number": 1,
        "required_fields": ["account_id", "created_at"],
    }
    records = [
        {
            "account_id": "A1",
        }
    ]

    with pytest.raises(ValueError, match="missing required fields"):
        validation.validate_dataset_stream(
            dataset,
            iter(records),
            non_empty_fields=[],
        )


def test_unknown_parent_reference_is_rejected():
    child_dataset = {
        "number": 40,
        "required_fields": ["event_id", "signup_journey_id"],
    }
    child_records = [
        {
            "event_id": "E1",
            "signup_journey_id": "J_MISSING",
        }
    ]

    with pytest.raises(ValueError, match="references unknown value"):
        validation.validate_reference_stream(
            child_dataset_metadata=child_dataset,
            records=iter(child_records),
            non_empty_fields=["signup_journey_id"],
            child_field="signup_journey_id",
            parent_values={"J1", "J2"},
        )
