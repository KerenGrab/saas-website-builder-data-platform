"""Dependency-aware PostgreSQL bulk loading for Part 9D."""

import logging
from itertools import chain

from psycopg import sql

from pipeline import (
    db,
    ingestion,
    load_plan,
    metadata,
    transformation,
)


logger = logging.getLogger(
    "saas_pipeline.loading"
)


class TargetNotEmptyError(RuntimeError):
    """Raised when a first canonical 9D load would write into existing data."""


class ReconciliationError(RuntimeError):
    """Raised when inserted data does not match the expected target state."""


def inspect_target_state(
    connection,
    target_tables=None,
):
    """Perform a read-only target-state inspection and return row counts.

    Production callers omit target_tables and therefore inspect the canonical
    49-table plan. Tests may pass a tiny isolated table list without changing
    production behaviour.
    """
    if target_tables is None:
        target_tables = (
            load_plan.get_target_tables_in_load_order()
        )

    db.validate_target_tables_exist(
        connection,
        target_tables,
    )

    return db.get_table_counts(
        connection,
        target_tables,
    )


def assert_target_is_empty(
    connection,
    target_tables=None,
):
    """Stop safely if any requested target table already contains rows."""
    counts = inspect_target_state(
        connection,
        target_tables=target_tables,
    )

    non_empty = {
        table_name: row_count
        for table_name, row_count
        in counts.items()
        if row_count != 0
    }

    if non_empty:
        details = ", ".join(
            f"{table_name}={row_count}"
            for table_name, row_count
            in sorted(
                non_empty.items()
            )
        )

        raise TargetNotEmptyError(
            "Part 9D full load was blocked before "
            "any write because the canonical target "
            f"is not empty: {details}. "
            "No TRUNCATE or DROP was executed."
        )

    return counts


def _get_copyable_target_columns(
    connection,
    table_name,
    source_field_names,
):
    """Resolve COPY columns and PostgreSQL metadata for the target table."""
    physical_columns = (
        db.get_target_table_columns(
            connection,
            table_name,
        )
    )

    copyable_columns = []
    nullable_columns = set()
    target_data_types = {}

    for column in physical_columns:
        column_name = column["name"]

        if column["generated"] == "ALWAYS":
            continue

        if column_name in source_field_names:
            copyable_columns.append(
                column_name
            )

            target_data_types[
                column_name
            ] = column["data_type"]

            if column["nullable"]:
                nullable_columns.add(
                    column_name
                )

            continue

        if (
            column["default"] is not None
            or column[
                "identity_generation"
            ] is not None
        ):
            continue

        raise transformation.MappingError(
            "Source data does not provide "
            f"required target column "
            f"'{table_name}.{column_name}'."
        )

    if not copyable_columns:
        raise transformation.MappingError(
            f"No copyable target columns "
            f"resolved for table "
            f"'{table_name}'."
        )

    return (
        tuple(copyable_columns),
        nullable_columns,
        target_data_types,
    )


def _build_copy_statement(
    table_name,
    target_columns,
):
    """Build COPY ... FROM STDIN using safe PostgreSQL identifiers."""
    return sql.SQL(
        "COPY {} ({}) FROM STDIN"
    ).format(
        sql.Identifier(
            db.TARGET_SCHEMA,
            table_name,
        ),
        sql.SQL(", ").join(
            sql.Identifier(
                column_name
            )
            for column_name
            in target_columns
        ),
    )


def _load_single_dataset(
    connection,
    contract,
    dataset_number,
):
    """Stream-transform and COPY one canonical dataset inside the transaction."""
    dataset_metadata = (
        metadata.get_dataset_by_number(
            contract,
            dataset_number,
        )
    )

    spec = load_plan.get_load_spec(
        dataset_number
    )

    source_records = (
        ingestion.iter_dataset_records(
            dataset_metadata
        )
    )

    try:
        first_record = next(
            source_records
        )

    except StopIteration as error:
        raise ReconciliationError(
            f"Dataset #{dataset_number} "
            "is empty but the frozen "
            "reference expects "
            f"{dataset_metadata['rows']} "
            "raw rows."
        ) from error

    (
        target_columns,
        nullable_columns,
        target_data_types,
    ) = _get_copyable_target_columns(
        connection=connection,
        table_name=(
            spec["target_table"]
        ),
        source_field_names=set(
            first_record
        ),
    )

    stats = (
        transformation.new_transform_stats()
    )

    target_ready_records = (
        transformation.iter_target_ready_records(
            dataset_number=
                dataset_number,
            source_format=
                dataset_metadata[
                    "format"
                ],
            records=chain(
                (first_record,),
                source_records,
            ),
            target_columns=
                target_columns,
            nullable_columns=
                nullable_columns,
            target_data_types=
                target_data_types,
            stats=stats,
        )
    )

    copy_statement = (
        _build_copy_statement(
            spec["target_table"],
            target_columns,
        )
    )

    try:
        with connection.cursor() as cursor:
            with cursor.copy(
                copy_statement
            ) as copy:
                for record in (
                    target_ready_records
                ):
                    copy.write_row(
                        tuple(
                            record[
                                column_name
                            ]
                            for column_name
                            in target_columns
                        )
                    )

    except (
        transformation.MappingError,
        transformation.DuplicatePayloadConflictError,
    ):
        raise

    except Exception as error:
        raise RuntimeError(
            f"Loading failed for Dataset "
            f"#{dataset_number} "
            f"'{dataset_metadata['dataset']}' "
            f"-> "
            f"'{spec['target_table']}'."
        ) from error

    expected_raw_rows = (
        dataset_metadata["rows"]
    )

    expected_duplicates = (
        spec[
            "expected_exact_duplicates"
        ]
    )

    expected_inserted_rows = (
        load_plan.expected_target_rows(
            dataset_metadata
        )
    )

    if (
        stats["raw_records"]
        != expected_raw_rows
    ):
        raise ReconciliationError(
            f"Dataset #{dataset_number} "
            "raw-row reconciliation "
            "failed: "
            f"expected "
            f"{expected_raw_rows}, "
            f"streamed "
            f"{stats['raw_records']}."
        )

    if (
        stats["duplicates_skipped"]
        != expected_duplicates
    ):
        raise ReconciliationError(
            f"Dataset #{dataset_number} "
            "duplicate reconciliation "
            "failed: "
            f"expected "
            f"{expected_duplicates}, "
            f"skipped "
            f"{stats['duplicates_skipped']}."
        )

    if (
        stats["records_emitted"]
        != expected_inserted_rows
    ):
        raise ReconciliationError(
            f"Dataset #{dataset_number} "
            "emitted-row reconciliation "
            "failed: "
            f"expected "
            f"{expected_inserted_rows}, "
            f"emitted "
            f"{stats['records_emitted']}."
        )

    return {
        "dataset_number":
            dataset_number,

        "source_dataset":
            dataset_metadata[
                "dataset"
            ],

        "target_table":
            spec[
                "target_table"
            ],

        "raw_rows":
            stats[
                "raw_records"
            ],

        "duplicates_skipped":
            stats[
                "duplicates_skipped"
            ],

        "inserted_rows":
            stats[
                "records_emitted"
            ],
    }


def _reconcile_loaded_targets(
    connection,
    load_results,
):
    """Verify target counts before the one atomic transaction is committed."""
    expected_by_table = {
        result["target_table"]:
            result["inserted_rows"]
        for result
        in load_results
    }

    actual_by_table = (
        db.get_table_counts(
            connection,
            expected_by_table.keys(),
        )
    )

    mismatches = []

    for (
        table_name,
        expected_rows,
    ) in expected_by_table.items():
        actual_rows = (
            actual_by_table[
                table_name
            ]
        )

        if (
            actual_rows
            != expected_rows
        ):
            mismatches.append(
                f"{table_name}: "
                f"expected="
                f"{expected_rows}, "
                f"actual="
                f"{actual_rows}"
            )

    if mismatches:
        raise ReconciliationError(
            "Post-load table-count "
            "reconciliation failed: "
            + "; ".join(
                mismatches
            )
        )

    actual_total = sum(
        actual_by_table.values()
    )

    if (
        actual_total
        != load_plan.EXPECTED_REFERENCE_TARGET_ROWS
    ):
        raise ReconciliationError(
            "Post-load total-row "
            "reconciliation failed: "
            f"expected "
            f"{load_plan.EXPECTED_REFERENCE_TARGET_ROWS}, "
            f"actual "
            f"{actual_total}."
        )

    return actual_by_table


def _expected_target_counts_from_contract(
    contract,
):
    """Return expected frozen-reference target counts keyed by target table."""
    expected = {}

    for dataset_number in (
        load_plan.iter_dataset_numbers_in_load_order()
    ):
        dataset_metadata = (
            metadata.get_dataset_by_number(
                contract,
                dataset_number,
            )
        )

        table_name = (
            load_plan.get_load_spec(
                dataset_number
            )[
                "target_table"
            ]
        )

        expected[
            table_name
        ] = (
            load_plan.expected_target_rows(
                dataset_metadata
            )
        )

    return expected


def _assert_target_counts_match(
    actual_by_table,
    expected_by_table,
):
    """Raise ReconciliationError when target counts differ from expectation."""
    mismatches = []

    for (
        table_name,
        expected_rows,
    ) in expected_by_table.items():
        actual_rows = (
            actual_by_table.get(
                table_name
            )
        )

        if (
            actual_rows
            != expected_rows
        ):
            mismatches.append(
                f"{table_name}: "
                f"expected="
                f"{expected_rows}, "
                f"actual="
                f"{actual_rows}"
            )

    if mismatches:
        raise ReconciliationError(
            "Target table-count "
            "reconciliation failed: "
            + "; ".join(
                mismatches
            )
        )

    actual_total = sum(
        actual_by_table.values()
    )

    expected_total = sum(
        expected_by_table.values()
    )

    if (
        actual_total
        != expected_total
    ):
        raise ReconciliationError(
            "Target total-row "
            "reconciliation failed: "
            f"expected "
            f"{expected_total}, "
            f"actual "
            f"{actual_total}."
        )


def reconcile_existing_target_state(
    connection,
    contract,
):
    """Read-only verification used before safely skipping a successful rerun."""
    expected = (
        _expected_target_counts_from_contract(
            contract
        )
    )

    actual = (
        inspect_target_state(
            connection,
            target_tables=
                tuple(expected),
        )
    )

    _assert_target_counts_match(
        actual,
        expected,
    )

    return actual


def load_all_datasets_in_transaction(
    connection,
    contract,
):
    """Load/reconcile all 49 datasets inside an already-owned transaction."""
    load_plan.validate_load_plan(
        contract
    )

    load_results = []

    for (
        group_number,
        group,
    ) in enumerate(
        load_plan.EXECUTION_GROUPS,
        start=1,
    ):
        print()

        print(
            f"Loading execution group "
            f"{group_number}/5..."
        )

        logger.info(
            "Loading execution group "
            "%s/5 started",
            group_number,
        )

        for dataset_number in group:
            spec = (
                load_plan.get_load_spec(
                    dataset_number
                )
            )

            print(
                f"  Dataset "
                f"#{dataset_number} -> "
                f"{spec['target_table']}..."
            )

            logger.info(
                "Dataset #%s -> %s "
                "load started",
                dataset_number,
                spec["target_table"],
            )

            result = (
                _load_single_dataset(
                    connection=
                        connection,
                    contract=
                        contract,
                    dataset_number=
                        dataset_number,
                )
            )

            load_results.append(
                result
            )

            print(
                f"    raw="
                f"{result['raw_rows']}, "
                f"duplicates_skipped="
                f"{result['duplicates_skipped']}, "
                f"inserted="
                f"{result['inserted_rows']}"
            )

            logger.info(
                "Dataset #%s load "
                "completed raw=%s "
                "duplicates_skipped=%s "
                "inserted=%s",
                dataset_number,
                result["raw_rows"],
                result[
                    "duplicates_skipped"
                ],
                result[
                    "inserted_rows"
                ],
            )

    print()

    print(
        "Running basic 9D "
        "post-load reconciliation "
        "before COMMIT..."
    )

    logger.info(
        "Post-load reconciliation "
        "started before COMMIT"
    )

    target_counts = (
        _reconcile_loaded_targets(
            connection,
            load_results,
        )
    )

    print(
        "Basic 9D reconciliation: OK"
    )

    logger.info(
        "Post-load reconciliation "
        "completed tables=%s "
        "status=PASS",
        len(target_counts),
    )

    return {
        "results":
            load_results,

        "target_counts":
            target_counts,

        "raw_rows":
            sum(
                result["raw_rows"]
                for result
                in load_results
            ),

        "duplicates_skipped":
            sum(
                result[
                    "duplicates_skipped"
                ]
                for result
                in load_results
            ),

        "inserted_rows":
            sum(
                result[
                    "inserted_rows"
                ]
                for result
                in load_results
            ),
    }


def load_all_datasets(
    connection,
    contract,
    *,
    before_commit=None,
):
    """Backward-compatible one-transaction Part 9D loader.

    Part 9F's rerun-aware orchestration calls
    load_all_datasets_in_transaction directly
    so SUCCESS metadata can commit atomically
    with target rows.
    """
    if not connection.autocommit:
        raise RuntimeError(
            "Part 9D loader requires "
            "a connection opened with "
            "autocommit=True so that "
            "the explicit transaction "
            "owns the single "
            "all-or-nothing load boundary."
        )

    load_plan.validate_load_plan(
        contract
    )

    assert_target_is_empty(
        connection
    )

    return db.run_atomic(
        connection,
        lambda active_connection: (
            load_all_datasets_in_transaction(
                active_connection,
                contract,
            )
        ),
        before_commit=
            before_commit,
    )