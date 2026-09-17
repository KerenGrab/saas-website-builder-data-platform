"""
Pre-load validation utilities for the SaaS data pipeline.

This module validates source records after ingestion and before
transformation or database loading.

The validation flow currently supports:

1. Structure validation
   - required fields must exist.

2. Basic value validation
   - explicitly selected non-empty fields must contain values.

3. Relationship validation
   - child references must point to known parent values.

The functions are designed to work with streaming iterators so that
large source datasets do not need to be loaded completely into memory.
"""


def _get_required_fields(dataset_metadata):
    """
    Read and validate required_fields from dataset metadata.

    Returns:
        list[str]:
            Structurally required source fields.
    """

    required_fields = dataset_metadata.get("required_fields")

    if not isinstance(required_fields, list):
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "does not define required_fields as a list."
        )

    if not required_fields:
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "does not define any required fields."
        )

    if len(required_fields) != len(set(required_fields)):
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "contains duplicate names in required_fields."
        )

    return required_fields


def _validate_non_empty_field_list(
    dataset_metadata,
    non_empty_fields,
):
    """
    Validate the configuration of non-empty fields.
    """

    if not isinstance(non_empty_fields, list):
        raise ValueError(
            "non_empty_fields must be provided as a list."
        )

    if len(non_empty_fields) != len(set(non_empty_fields)):
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "contains duplicate names in non_empty_fields."
        )


def _validate_single_record(
    dataset_metadata,
    record,
    record_number,
    required_fields,
    non_empty_fields,
):
    """
    Validate the structure and selected values of one source record.
    """

    if not isinstance(record, dict):
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            f"record #{record_number} is not a dictionary."
        )

    # ------------------------------------------------------------------
    # Structure validation
    # ------------------------------------------------------------------

    missing_fields = [
        field
        for field in required_fields
        if field not in record
    ]

    if missing_fields:
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            f"record #{record_number} is missing required fields: "
            f"{missing_fields}"
        )

    # ------------------------------------------------------------------
    # Value validation
    # ------------------------------------------------------------------

    for field in non_empty_fields:

        if field not in record:
            raise ValueError(
                f"Dataset #{dataset_metadata['number']} "
                f"record #{record_number} does not contain "
                f"non-empty field '{field}'."
            )

        value = record[field]

        if value is None:
            raise ValueError(
                f"Dataset #{dataset_metadata['number']} "
                f"record #{record_number} has no value "
                f"for non-empty field '{field}'."
            )

        if isinstance(value, str) and not value.strip():
            raise ValueError(
                f"Dataset #{dataset_metadata['number']} "
                f"record #{record_number} has an empty value "
                f"for non-empty field '{field}'."
            )


def validate_dataset_stream(
    dataset_metadata,
    records,
    non_empty_fields,
):
    """
    Validate one dataset while consuming its records as a stream.

    The function does not store the complete dataset.

    Args:
        dataset_metadata (dict):
            Metadata for one dataset.

        records:
            Iterator yielding source records.

        non_empty_fields (list[str]):
            Fields explicitly required to contain values.

    Returns:
        int:
            Number of records successfully validated.
    """

    required_fields = _get_required_fields(
        dataset_metadata
    )

    _validate_non_empty_field_list(
        dataset_metadata,
        non_empty_fields,
    )

    record_count = 0

    for record_number, record in enumerate(
        records,
        start=1,
    ):
        _validate_single_record(
            dataset_metadata=dataset_metadata,
            record=record,
            record_number=record_number,
            required_fields=required_fields,
            non_empty_fields=non_empty_fields,
        )

        record_count += 1

    return record_count


def validate_dataset_and_collect_values(
    dataset_metadata,
    records,
    non_empty_fields,
    collect_field,
):
    """
    Validate a streamed dataset while collecting one field into a set.

    This is useful for parent datasets in relationship validation.

    For example:

        Dataset #39
        signup_journey_id

    can be validated while its known journey IDs are collected.

    Only the selected field values are retained in memory.
    The complete dataset is not retained.

    Args:
        dataset_metadata (dict):
            Metadata for the parent dataset.

        records:
            Iterator yielding parent records.

        non_empty_fields (list[str]):
            Fields explicitly required to contain values.

        collect_field (str):
            Field whose values should be collected.

    Returns:
        tuple:
            (
                number_of_records,
                set_of_collected_values
            )
    """

    required_fields = _get_required_fields(
        dataset_metadata
    )

    _validate_non_empty_field_list(
        dataset_metadata,
        non_empty_fields,
    )

    collected_values = set()

    record_count = 0

    for record_number, record in enumerate(
        records,
        start=1,
    ):
        _validate_single_record(
            dataset_metadata=dataset_metadata,
            record=record,
            record_number=record_number,
            required_fields=required_fields,
            non_empty_fields=non_empty_fields,
        )

        if collect_field not in record:
            raise ValueError(
                f"Dataset #{dataset_metadata['number']} "
                f"record #{record_number} does not contain "
                f"collection field '{collect_field}'."
            )

        value = record[collect_field]

        if value is None:
            raise ValueError(
                f"Dataset #{dataset_metadata['number']} "
                f"record #{record_number} has no value "
                f"for collection field '{collect_field}'."
            )

        if isinstance(value, str) and not value.strip():
            raise ValueError(
                f"Dataset #{dataset_metadata['number']} "
                f"record #{record_number} has an empty value "
                f"for collection field '{collect_field}'."
            )

        collected_values.add(value)

        record_count += 1

    return record_count, collected_values


def validate_reference_stream(
    child_dataset_metadata,
    records,
    non_empty_fields,
    child_field,
    parent_values,
):
    """
    Validate a streamed child dataset against known parent values.

    Every value from child_field must appear in parent_values.

    The child dataset is consumed one record at a time and is not
    stored completely in memory.

    Args:
        child_dataset_metadata (dict):
            Metadata for the child dataset.

        records:
            Iterator yielding child records.

        non_empty_fields (list[str]):
            Child fields explicitly required to contain values.

        child_field (str):
            Field containing the parent reference.

        parent_values (set):
            Valid parent values collected from the parent dataset.

    Returns:
        int:
            Number of child records successfully validated.
    """

    required_fields = _get_required_fields(
        child_dataset_metadata
    )

    _validate_non_empty_field_list(
        child_dataset_metadata,
        non_empty_fields,
    )

    record_count = 0

    for record_number, record in enumerate(
        records,
        start=1,
    ):
        # First perform normal structure/value validation.
        _validate_single_record(
            dataset_metadata=child_dataset_metadata,
            record=record,
            record_number=record_number,
            required_fields=required_fields,
            non_empty_fields=non_empty_fields,
        )

        # Then perform relationship validation.
        if child_field not in record:
            raise ValueError(
                f"Dataset #{child_dataset_metadata['number']} "
                f"record #{record_number} does not contain "
                f"relationship field '{child_field}'."
            )

        child_value = record[child_field]

        if child_value is None:
            raise ValueError(
                f"Dataset #{child_dataset_metadata['number']} "
                f"record #{record_number} has no value "
                f"for relationship field '{child_field}'."
            )

        if isinstance(child_value, str) and not child_value.strip():
            raise ValueError(
                f"Dataset #{child_dataset_metadata['number']} "
                f"record #{record_number} has an empty value "
                f"for relationship field '{child_field}'."
            )

        if child_value not in parent_values:
            raise ValueError(
                f"Dataset #{child_dataset_metadata['number']} "
                f"record #{record_number} references unknown "
                f"value '{child_value}' "
                f"through field '{child_field}'."
            )

        record_count += 1

    return record_count