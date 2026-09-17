import pytest

from pipeline import transformation


def test_first_event_delivery_is_emitted():
    event = {
        "event_id": "E1",
        "event_type": "demo",
    }

    assert transformation.should_emit_event(
        40,
        event,
        {},
    ) is True


def test_exact_duplicate_event_is_skipped_and_counted():
    event = {
        "event_id": "E1",
        "event_type": "demo",
    }
    stats = transformation.new_transform_stats()

    results = list(
        transformation.iter_target_ready_records(
            dataset_number=40,
            source_format="jsonl",
            records=iter([event, dict(event)]),
            target_columns=("event_id", "event_type"),
            nullable_columns=set(),
            target_data_types={
                "event_id": "text",
                "event_type": "text",
            },
            stats=stats,
        )
    )

    assert results == [event]
    assert stats == {
        "raw_records": 2,
        "records_emitted": 1,
        "duplicates_skipped": 1,
    }


def test_conflicting_duplicate_event_is_rejected():
    first = {
        "event_id": "E1",
        "event_type": "page_view",
    }
    conflicting = {
        "event_id": "E1",
        "event_type": "link_click",
    }
    seen = {}

    assert transformation.should_emit_event(
        40,
        first,
        seen,
    ) is True

    with pytest.raises(
        transformation.DuplicatePayloadConflictError,
        match="conflicting payloads",
    ):
        transformation.should_emit_event(
            40,
            conflicting,
            seen,
        )
