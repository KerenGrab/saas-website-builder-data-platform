"""Record-level Part 9D transformations and exact-event deduplication."""

import hashlib
import json
from decimal import Decimal, InvalidOperation

from pipeline import load_plan


class MappingError(ValueError):
    """Raised when a source record cannot be mapped safely to its target."""


class DuplicatePayloadConflictError(ValueError):
    """Raised when one event_id is delivered with conflicting payloads."""


INTEGER_DATA_TYPES = {
    "smallint",
    "integer",
    "bigint",
}


def new_transform_stats():
    """Create mutable counters used while a dataset is streamed."""
    return {
        "raw_records": 0,
        "records_emitted": 0,
        "duplicates_skipped": 0,
    }


def canonical_payload_digest(record):
    """Return a stable SHA256 digest for the semantic JSON object payload."""
    canonical_json = json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).digest()


def should_emit_event(
    dataset_number,
    record,
    seen_event_payloads,
):
    """Apply the canonical event_id duplicate policy to one JSONL record."""
    event_id = record.get("event_id")

    if (
        not isinstance(event_id, str)
        or not event_id.strip()
    ):
        raise MappingError(
            f"Dataset #{dataset_number} cannot deduplicate "
            "a record without a non-empty event_id."
        )

    digest = canonical_payload_digest(record)

    previous_digest = (
        seen_event_payloads.get(event_id)
    )

    if previous_digest is None:
        seen_event_payloads[event_id] = digest
        return True

    if previous_digest == digest:
        return False

    raise DuplicatePayloadConflictError(
        f"Dataset #{dataset_number} contains "
        f"conflicting payloads for event_id '{event_id}'."
    )


def normalize_value_for_target_type(
    dataset_number,
    column_name,
    value,
    data_type,
):
    """Safely normalize a source value for the PostgreSQL target type."""
    if value is None:
        return None

    if data_type not in INTEGER_DATA_TYPES:
        return value

    if isinstance(value, bool):
        raise MappingError(
            f"Dataset #{dataset_number} column '{column_name}' "
            f"cannot safely convert boolean value {value!r} "
            f"to PostgreSQL {data_type}."
        )

    if isinstance(value, int):
        return value

    try:
        decimal_value = Decimal(str(value).strip())

    except (InvalidOperation, ValueError) as error:
        raise MappingError(
            f"Dataset #{dataset_number} column '{column_name}' "
            f"cannot convert value {value!r} "
            f"to PostgreSQL {data_type}."
        ) from error

    if decimal_value != decimal_value.to_integral_value():
        raise MappingError(
            f"Dataset #{dataset_number} column '{column_name}' "
            f"contains non-integral value {value!r}, "
            f"but PostgreSQL target type is {data_type}."
        )

    return int(decimal_value)


def transform_record(
    dataset_number,
    source_format,
    record,
    target_columns,
    nullable_columns,
    target_data_types,
):
    """Transform one accepted source record into a target-ready dictionary."""
    if not isinstance(record, dict):
        raise MappingError(
            f"Dataset #{dataset_number} source record "
            "is not a dictionary."
        )

    spec = load_plan.get_load_spec(
        dataset_number
    )

    drop_fields = set(
        spec["drop_fields"]
    )

    target_column_set = set(
        target_columns
    )

    source_fields = set(record)

    unexpected_source_fields = (
        source_fields
        - target_column_set
        - drop_fields
    )

    if unexpected_source_fields:
        raise MappingError(
            f"Dataset #{dataset_number} contains source "
            "fields with no canonical target mapping: "
            f"{sorted(unexpected_source_fields)}"
        )

    missing_target_fields = (
        target_column_set
        - source_fields
    )

    if missing_target_fields:
        raise MappingError(
            f"Dataset #{dataset_number} is missing target "
            f"fields required by PostgreSQL table "
            f"'{spec['target_table']}': "
            f"{sorted(missing_target_fields)}"
        )

    transformed = {}

    for column_name in target_columns:

        value = record[column_name]

        # csv.DictReader represents an empty CSV field as "".
        # Convert it to SQL NULL only when the real PostgreSQL
        # target column is nullable.
        if (
            source_format == "csv"
            and value == ""
            and column_name in nullable_columns
        ):
            value = None

        value = normalize_value_for_target_type(
            dataset_number=dataset_number,
            column_name=column_name,
            value=value,
            data_type=target_data_types[column_name],
        )

        transformed[column_name] = value

    return transformed


def iter_target_ready_records(
    dataset_number,
    source_format,
    records,
    target_columns,
    nullable_columns,
    target_data_types,
    stats,
):
    """Stream source records through projection, NULL handling and dedup."""
    spec = load_plan.get_load_spec(
        dataset_number
    )

    seen_event_payloads = (
        {}
        if spec["deduplicate_by_event_id"]
        else None
    )

    for record in records:

        stats["raw_records"] += 1

        if seen_event_payloads is not None:

            if not should_emit_event(
                dataset_number,
                record,
                seen_event_payloads,
            ):
                stats["duplicates_skipped"] += 1
                continue

        transformed = transform_record(
            dataset_number=dataset_number,
            source_format=source_format,
            record=record,
            target_columns=target_columns,
            nullable_columns=nullable_columns,
            target_data_types=target_data_types,
        )

        stats["records_emitted"] += 1

        yield transformed


def run_transformation_self_check():
    """Run small in-memory checks without opening PostgreSQL or source files."""
    membership_source = {
        "event_id": "EV_1",
        "membership_id": "MEM_1",
        "user_id": "USR_1",
        "account_id": "ACC_1",
        "event_type": "joined",
        "event_time": "2025-01-01T00:00:00Z",
    }

    membership_target = transform_record(
        dataset_number=8,
        source_format="csv",
        record=membership_source,
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

    if set(membership_target) != {
        "event_id",
        "membership_id",
        "event_type",
        "event_time",
    }:
        raise AssertionError(
            "Dataset #8 projection self-check failed."
        )

    linkage_source = {
        "visitor_member_link_id": "VML_1",
        "visitor_id": "VIS_1",
        "member_id": "MEMBER_1",
        "website_id": "WEB_1",
        "valid_from": "2025-01-01T00:00:00Z",
        "valid_to": "",
    }

    linkage_target = transform_record(
        dataset_number=36,
        source_format="csv",
        record=linkage_source,
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

    if "website_id" in linkage_target:
        raise AssertionError(
            "Dataset #36 projection self-check failed."
        )

    if linkage_target["valid_to"] is not None:
        raise AssertionError(
            "CSV nullable-field normalization self-check failed."
        )

    integer_target = transform_record(
        dataset_number=30,
        source_format="csv",
        record={
            "rating_value": "5.0",
        },
        target_columns=(
            "rating_value",
        ),
        nullable_columns=set(),
        target_data_types={
            "rating_value": "integer",
        },
    )

    if integer_target["rating_value"] != 5:
        raise AssertionError(
            "Integer type normalization self-check failed."
        )

    seen = {}

    event = {
        "event_id": "EV_DUP_1",
        "event_type": "demo",
        "event_time": "2025-01-01T00:00:00Z",
    }

    if not should_emit_event(
        40,
        event,
        seen,
    ):
        raise AssertionError(
            "First event delivery should be emitted."
        )

    if should_emit_event(
        40,
        dict(event),
        seen,
    ):
        raise AssertionError(
            "Exact duplicate delivery should be skipped."
        )

    conflicting_event = dict(event)

    conflicting_event[
        "event_type"
    ] = "different"

    try:
        should_emit_event(
            40,
            conflicting_event,
            seen,
        )

    except DuplicatePayloadConflictError:
        pass

    else:
        raise AssertionError(
            "Conflicting duplicate payload should "
            "raise an exception."
        )

    return {
        "dataset_8_projection": "OK",
        "dataset_36_projection": "OK",
        "csv_nullable_normalization": "OK",
        "integer_type_normalization": "OK",
        "exact_duplicate_skip": "OK",
        "duplicate_conflict_detection": "OK",
    }