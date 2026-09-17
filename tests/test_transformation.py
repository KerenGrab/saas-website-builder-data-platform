from pipeline import transformation


def test_dataset_8_projection_removes_redundant_identity_fields():
    source = {
        "event_id": "EV_1",
        "membership_id": "MEM_1",
        "user_id": "USR_1",
        "account_id": "ACC_1",
        "event_type": "joined",
        "event_time": "2025-01-01T00:00:00Z",
    }

    result = transformation.transform_record(
        dataset_number=8,
        source_format="csv",
        record=source,
        target_columns=(
            "event_id",
            "membership_id",
            "event_type",
            "event_time",
        ),
        nullable_columns=set(),
        target_data_types={
            "event_id": "text",
            "membership_id": "text",
            "event_type": "text",
            "event_time": "timestamp with time zone",
        },
    )

    assert result == {
        "event_id": "EV_1",
        "membership_id": "MEM_1",
        "event_type": "joined",
        "event_time": "2025-01-01T00:00:00Z",
    }


def test_dataset_36_projection_and_nullable_csv_handling():
    source = {
        "visitor_member_link_id": "VML_1",
        "visitor_id": "VIS_1",
        "member_id": "MEMBER_1",
        "website_id": "WEB_1",
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_to": "",
    }

    result = transformation.transform_record(
        dataset_number=36,
        source_format="csv",
        record=source,
        target_columns=(
            "visitor_member_link_id",
            "visitor_id",
            "member_id",
            "valid_from",
            "valid_to",
        ),
        nullable_columns={"valid_to"},
        target_data_types={
            "visitor_member_link_id": "text",
            "visitor_id": "text",
            "member_id": "text",
            "valid_from": "timestamp with time zone",
            "valid_to": "timestamp with time zone",
        },
    )

    assert "website_id" not in result
    assert result["valid_to"] is None
