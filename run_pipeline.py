"""Main entrypoint for the SaaS Website Builder data pipeline.

Part 9G adds persistent logging and one durable run-history row per CLI
execution while preserving the already-verified Part 9F pipeline behaviour.
"""

import argparse
import logging
import time

from pipeline import (
    config,
    data_quality,
    db,
    ingestion,
    integrity,
    load_plan,
    loading,
    logging_config,
    metadata,
    paths,
    rerun,
    run_history,
    transformation,
    validation,
)


logger = logging.getLogger(
    "saas_pipeline.runner"
)


MODES = (
    "validate",
    "plan-check",
    "transform-check",
    "target-check",
    "dq",
    "full-load",
)


def parse_args(
    argv=None,
):
    parser = argparse.ArgumentParser(
        description=(
            "SaaS Website Builder "
            "canonical data pipeline"
        )
    )

    parser.add_argument(
        "--mode",
        choices=MODES,
        default="validate",
        help=(
            "validate "
            "(default, no business-data writes), "
            "plan-check, transform-check, "
            "target-check "
            "(read-only business-data check), "
            "dq "
            "(read-only Data Quality), "
            "or full-load "
            "(writes to PostgreSQL business tables)"
        ),
    )

    parser.add_argument(
        "--batch-id",
        default=None,
        help=(
            "Logical batch identifier "
            "used by Part 9F rerun safety. "
            "If omitted, a stable id "
            "is derived from contract_version."
        ),
    )

    return parser.parse_args(
        argv
    )


def print_startup_configuration(
    mode,
):
    print(
        "Starting SaaS data pipeline..."
    )

    print(
        f"Mode: {mode}"
    )

    print(
        f"Database host: "
        f"{config.DB_HOST}"
    )

    print(
        f"Database port: "
        f"{config.DB_PORT}"
    )

    print(
        f"Database name: "
        f"{config.DB_NAME}"
    )

    print(
        f"Database user: "
        f"{config.DB_USER}"
    )

    print(
        "Database password configured: "
        f"{config.DB_PASSWORD is not None}"
    )

    print(
        f"Project root: "
        f"{paths.PROJECT_ROOT}"
    )

    print(
        f"Source root: "
        f"{paths.SOURCE_ROOT}"
    )

    print(
        f"Raw source root: "
        f"{paths.RAW_ROOT}"
    )

    print(
        f"Input contract path: "
        f"{paths.INPUT_CONTRACT_PATH}"
    )

    input_contract_exists = (
        paths.INPUT_CONTRACT_PATH
        is not None
        and paths.INPUT_CONTRACT_PATH.is_file()
    )

    raw_root_exists = (
        paths.RAW_ROOT
        is not None
        and paths.RAW_ROOT.is_dir()
    )

    print(
        f"Input contract exists: "
        f"{input_contract_exists}"
    )

    print(
        f"Raw source directory exists: "
        f"{raw_root_exists}"
    )


def load_and_validate_startup_metadata():
    """Load the frozen contract and verify all 49 declared source files."""
    print(
        "Loading final input contract..."
    )

    contract = (
        metadata.load_input_contract()
    )

    print(
        f"Contract version: "
        f"{contract['contract_version']}"
    )

    print(
        f"Contract status: "
        f"{contract['status']}"
    )

    print(
        f"Datasets expected: "
        f"{contract['datasets_expected']}"
    )

    print(
        f"Datasets generated: "
        f"{contract['datasets_generated']}"
    )

    print(
        f"Dataset count: "
        f"{contract['dataset_count']}"
    )

    print(
        f"Dataset entries loaded: "
        f"{len(contract['datasets'])}"
    )

    print(
        "Final input contract: OK"
    )

    print(
        "Checking canonical source files..."
    )

    source_file_count = (
        metadata.validate_source_files(
            contract
        )
    )

    print(
        f"Canonical source files found: "
        f"{source_file_count}/49"
    )

    print(
        "Canonical source files: OK"
    )

    logger.info(
        "Input contract loaded and "
        "source-file availability verified "
        "datasets=%s",
        source_file_count,
    )

    return contract


def run_full_structural_and_integrity_scan(
    contract,
):
    """Stream, structurally validate, and integrity-check all 49 datasets."""
    print()

    print(
        "Starting full 49-dataset "
        "structural and integrity scan..."
    )

    logger.info(
        "Validation stage started: "
        "structural + frozen integrity scan"
    )

    datasets_validated = 0
    total_records_scanned = 0
    row_counts_verified = 0
    hashes_verified = 0

    expected_total_records = sum(
        dataset["rows"]
        for dataset
        in contract["datasets"]
    )

    print(
        f"Frozen reference rows expected: "
        f"{expected_total_records}"
    )

    for dataset_number in range(
        1,
        50,
    ):
        dataset_metadata = (
            metadata.get_dataset_by_number(
                contract,
                dataset_number,
            )
        )

        dataset_name = (
            dataset_metadata[
                "dataset"
            ]
        )

        dataset_format = (
            dataset_metadata[
                "format"
            ]
        )

        print(
            f"Scanning Dataset "
            f"#{dataset_number}: "
            f"{dataset_name} "
            f"({dataset_format})..."
        )

        record_count = (
            validation.validate_dataset_stream(
                dataset_metadata=
                    dataset_metadata,
                records=
                    ingestion.iter_dataset_records(
                        dataset_metadata
                    ),
                non_empty_fields=[],
            )
        )

        datasets_validated += 1

        total_records_scanned += (
            record_count
        )

        integrity.validate_frozen_reference_integrity(
            dataset_metadata=
                dataset_metadata,
            actual_row_count=
                record_count,
        )

        row_counts_verified += 1
        hashes_verified += 1

        print(
            f"Dataset "
            f"#{dataset_number}: "
            f"{record_count} records, "
            "row count OK, "
            "SHA256 OK"
        )

        logger.info(
            "Dataset #%s "
            "validation passed "
            "records=%s "
            "row_count=PASS "
            "sha256=PASS",
            dataset_number,
            record_count,
        )

    print()

    print(
        f"Datasets structurally validated: "
        f"{datasets_validated}/49"
    )

    print(
        f"Total records scanned: "
        f"{total_records_scanned}"
    )

    print(
        f"Frozen reference rows expected: "
        f"{expected_total_records}"
    )

    if (
        total_records_scanned
        != expected_total_records
    ):
        raise ValueError(
            "Full-package row-count mismatch. "
            f"Expected "
            f"{expected_total_records}, "
            f"but scanned "
            f"{total_records_scanned}."
        )

    print(
        f"Reference row counts verified: "
        f"{row_counts_verified}/49"
    )

    print(
        f"SHA256 hashes verified: "
        f"{hashes_verified}/49"
    )

    print(
        "Full structural scan: OK"
    )

    print(
        "Frozen input integrity: OK"
    )

    logger.info(
        "Validation structural/integrity "
        "scan completed "
        "datasets=%s records=%s hashes=%s",
        datasets_validated,
        total_records_scanned,
        hashes_verified,
    )

    return (
        datasets_validated,
        total_records_scanned,
        row_counts_verified,
        hashes_verified,
    )


def run_signup_relationship_validation(
    contract,
):
    """Run the demonstrated #40.signup_journey_id -> #39 relationship check."""
    print()

    print(
        "Starting signup journey "
        "relationship validation..."
    )

    logger.info(
        "Relationship validation started: "
        "dataset #40 -> dataset #39"
    )

    parent_metadata = (
        metadata.get_dataset_by_number(
            contract,
            39,
        )
    )

    print(
        f"Streaming parent Dataset #39: "
        f"{parent_metadata['dataset']}..."
    )

    (
        parent_record_count,
        parent_journey_ids,
    ) = (
        validation.validate_dataset_and_collect_values(
            dataset_metadata=
                parent_metadata,
            records=
                ingestion.iter_dataset_records(
                    parent_metadata
                ),
            non_empty_fields=[
                "signup_journey_id",
            ],
            collect_field=
                "signup_journey_id",
        )
    )

    print(
        f"Dataset #39 records validated: "
        f"{parent_record_count}"
    )

    print(
        "Parent signup_journey_id "
        "values collected: "
        f"{len(parent_journey_ids)}"
    )

    child_metadata = (
        metadata.get_dataset_by_number(
            contract,
            40,
        )
    )

    print(
        f"Streaming child Dataset #40: "
        f"{child_metadata['dataset']}..."
    )

    print(
        "Checking relationship: "
        "#40.signup_journey_id -> "
        "#39.signup_journey_id..."
    )

    child_record_count = (
        validation.validate_reference_stream(
            child_dataset_metadata=
                child_metadata,
            records=
                ingestion.iter_dataset_records(
                    child_metadata
                ),
            non_empty_fields=[
                "event_id",
                "signup_journey_id",
                "event_type",
                "event_time",
            ],
            child_field=
                "signup_journey_id",
            parent_values=
                parent_journey_ids,
        )
    )

    print(
        "Dataset #40 records "
        "relationship-validated: "
        f"{child_record_count}"
    )

    print(
        "Signup journey "
        "relationship validation: OK"
    )

    logger.info(
        "Relationship validation "
        "completed child_records=%s "
        "status=PASS",
        child_record_count,
    )

    return child_record_count


def run_part_9c_preload_gate(
    contract,
):
    """Run the already-closed 9C validation/integrity gate before writes."""
    (
        datasets_validated,
        total_records_scanned,
        row_counts_verified,
        hashes_verified,
    ) = (
        run_full_structural_and_integrity_scan(
            contract
        )
    )

    relationship_records_validated = (
        run_signup_relationship_validation(
            contract
        )
    )

    return {
        "validation_status":
            "PASS",

        "datasets_expected":
            contract[
                "dataset_count"
            ],

        "datasets_processed":
            datasets_validated,

        "raw_records_scanned":
            total_records_scanned,

        "row_counts_verified":
            row_counts_verified,

        "hashes_verified":
            hashes_verified,

        "relationship_records_validated":
            relationship_records_validated,
    }


def run_plan_check(
    contract,
):
    """Validate the complete 49-dataset load plan without business-data writes."""
    print()

    print(
        "Checking canonical "
        "Part 9D load plan..."
    )

    logger.info(
        "Load-plan check started"
    )

    summary = (
        load_plan.validate_load_plan(
            contract
        )
    )

    print(
        f"Load plan datasets: "
        f"{summary['datasets']}/49"
    )

    print(
        f"Execution groups: "
        f"{summary['execution_groups']}"
    )

    print(
        f"Reference raw rows: "
        f"{summary['raw_rows']}"
    )

    print(
        "Expected physical target rows: "
        f"{summary['expected_target_rows']}"
    )

    print(
        f"Projection cases: "
        f"{summary['projection_cases']}"
    )

    print(
        "Duplicate-aware JSONL streams: "
        f"{summary['duplicate_aware_streams']}"
    )

    print(
        "Expected exact duplicate "
        "deliveries: "
        f"{summary['expected_exact_duplicates']}"
    )

    print(
        "Load plan: OK"
    )

    logger.info(
        "Load-plan check completed "
        "datasets=%s groups=%s "
        "status=PASS",
        summary["datasets"],
        summary["execution_groups"],
    )

    return summary


def run_transform_check():
    """Run small in-memory 9D transformation checks with no business DB access."""
    print()

    print(
        "Running transformation-only "
        "self-checks..."
    )

    logger.info(
        "Transformation "
        "self-check stage started"
    )

    results = (
        transformation.run_transformation_self_check()
    )

    for (
        check_name,
        status,
    ) in results.items():
        print(
            f"{check_name}: "
            f"{status}"
        )

    print(
        "Transformation self-checks: OK"
    )

    logger.info(
        "Transformation self-check "
        "stage completed "
        "checks=%s status=PASS",
        len(results),
    )

    return results


def run_target_check(
    *,
    raise_on_non_empty=False,
):
    """Inspect all 49 target tables using SELECT-only business-data operations."""
    print()

    print(
        "Checking PostgreSQL "
        "target state "
        "(read-only)..."
    )

    logger.info(
        "Target-state check started"
    )

    connection = (
        db.open_connection(
            autocommit=True
        )
    )

    try:
        counts = (
            loading.inspect_target_state(
                connection
            )
        )

    finally:
        connection.close()

    non_empty = {
        table_name: row_count
        for (
            table_name,
            row_count,
        ) in counts.items()
        if row_count != 0
    }

    print(
        f"Target tables found: "
        f"{len(counts)}/49"
    )

    print(
        f"Empty target tables: "
        f"{len(counts) - len(non_empty)}/49"
    )

    print(
        f"Non-empty target tables: "
        f"{len(non_empty)}/49"
    )

    if non_empty:
        print(
            "Existing canonical "
            "target data detected:"
        )

        for (
            table_name,
            row_count,
        ) in sorted(
            non_empty.items()
        ):
            print(
                f"  {table_name}: "
                f"{row_count}"
            )

        print(
            "Target ready for first "
            "canonical 9D load: NO"
        )

        print(
            "No destructive reset "
            "was performed."
        )

        logger.info(
            "Target-state check completed "
            "tables=%s non_empty=%s",
            len(counts),
            len(non_empty),
        )

        if raise_on_non_empty:
            details = ", ".join(
                f"{table_name}="
                f"{row_count}"
                for (
                    table_name,
                    row_count,
                ) in sorted(
                    non_empty.items()
                )
            )

            raise (
                loading.TargetNotEmptyError(
                    "Full load blocked "
                    "before any write because "
                    "target tables already "
                    "contain data: "
                    f"{details}."
                )
            )

    else:
        print(
            "Target ready for first "
            "canonical 9D load: YES"
        )

        logger.info(
            "Target-state check completed "
            "tables=%s non_empty=0",
            len(counts),
        )

    return counts


def run_dq_mode(
    *,
    capture_summary=False,
):
    """Run Part 9E Data Quality checks against the existing loaded database."""
    print()

    print(
        "DATA QUALITY MODE SELECTED"
    )

    print(
        "Running read-only checks "
        "against the existing "
        "PostgreSQL data..."
    )

    logger.info(
        "DQ stage started"
    )

    target_tables = (
        load_plan.get_target_tables_in_load_order()
    )

    connection = (
        db.open_connection(
            autocommit=True
        )
    )

    try:
        db.validate_target_tables_exist(
            connection,
            target_tables,
        )

        print(
            f"Target tables found: "
            f"{len(target_tables)}/49"
        )

        summary = (
            data_quality.run_data_quality_checks(
                connection
            )
        )

    finally:
        connection.close()

    print()

    print(
        "Data Quality Summary"
    )

    print(
        "--------------------"
    )

    print(
        f"Rules executed: "
        f"{summary['rules_executed']}"
    )

    print(
        f"PASS: "
        f"{summary['pass_count']}"
    )

    print(
        f"FAIL: "
        f"{summary['fail_count']}"
    )

    print(
        f"Total violations: "
        f"{summary['total_violations']}"
    )

    print()

    exit_code = (
        data_quality.exit_code_from_summary(
            summary
        )
    )

    dq_status = (
        "PASS"
        if exit_code == 0
        else "FAIL"
    )

    print(
        f"Overall DQ Status: "
        f"{dq_status}"
    )

    logger.info(
        "DQ stage completed "
        "rules=%s pass=%s fail=%s "
        "violations=%s dq_status=%s",
        summary["rules_executed"],
        summary["pass_count"],
        summary["fail_count"],
        summary["total_violations"],
        dq_status,
    )

    if capture_summary:
        return (
            exit_code,
            summary,
        )

    return exit_code


def run_validation_mode(
    contract,
):
    """Preserve the existing non-destructive 9C default business-data behavior."""
    summary = (
        run_part_9c_preload_gate(
            contract
        )
    )

    print()

    print(
        "Checking PostgreSQL connection..."
    )

    db.check_connection()

    print(
        "PostgreSQL connection: OK"
    )

    print()

    print(
        "Part 9C current pre-load "
        "validation flow: OK"
    )

    print(
        "No PostgreSQL business-data "
        "writes were performed."
    )

    logger.info(
        "Validation mode "
        "completed status=PASS"
    )

    return summary


def _apply_validation_evidence(
    evidence,
    summary,
):
    if (
        evidence is None
        or summary is None
    ):
        return

    evidence[
        "validation_status"
    ] = (
        summary[
            "validation_status"
        ]
    )

    evidence[
        "datasets_expected"
    ] = (
        summary[
            "datasets_expected"
        ]
    )

    evidence[
        "datasets_processed"
    ] = (
        summary[
            "datasets_processed"
        ]
    )

    evidence[
        "raw_records_scanned"
    ] = (
        summary[
            "raw_records_scanned"
        ]
    )


def run_full_load(
    contract,
    *,
    batch_id=None,
    evidence=None,
):
    """Execute the complete rerun-aware Part 9D/9F full load safely."""
    print()

    print(
        "FULL LOAD MODE SELECTED"
    )

    print(
        "PostgreSQL business-data "
        "writes will occur only after "
        "all pre-load gates pass."
    )

    logger.info(
        "Full-load mode started"
    )

    if evidence is not None:
        evidence[
            "current_stage"
        ] = "validation"

    validation_summary = (
        run_part_9c_preload_gate(
            contract
        )
    )

    _apply_validation_evidence(
        evidence,
        validation_summary,
    )

    if evidence is not None:
        evidence[
            "current_stage"
        ] = "load_plan"

    run_plan_check(
        contract
    )

    resolved_batch_id = (
        rerun.resolve_batch_id(
            contract,
            batch_id,
        )
    )

    fingerprint = (
        rerun.calculate_batch_fingerprint(
            contract
        )
    )

    if evidence is not None:
        evidence[
            "batch_id"
        ] = resolved_batch_id

        evidence[
            "fingerprint"
        ] = fingerprint

        evidence[
            "current_stage"
        ] = "rerun_check"

    logging_config.set_batch_id(
        resolved_batch_id
    )

    print()

    print(
        f"Batch ID: "
        f"{resolved_batch_id}"
    )

    print(
        f"Batch fingerprint: "
        f"{fingerprint}"
    )

    logger.info(
        "Rerun identity resolved "
        "fingerprint=%s",
        fingerprint,
    )

    connection = (
        db.open_connection(
            autocommit=True
        )
    )

    def pre_write_check(
        active_connection,
    ):
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "target_safety"

        result = (
            loading.assert_target_is_empty(
                active_connection
            )
        )

        if evidence is not None:
            evidence[
                "current_stage"
            ] = "rerun_check"

        return result

    def verify_existing_state(
        active_connection,
    ):
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "reconciliation"

        counts = (
            loading.reconcile_existing_target_state(
                active_connection,
                contract,
            )
        )

        if evidence is not None:
            evidence[
                "target_tables_reconciled"
            ] = len(counts)

            evidence[
                "duplicates_skipped"
            ] = 0

            evidence[
                "rows_loaded"
            ] = 0

            evidence[
                "current_stage"
            ] = "rerun_check"

        return counts

    def work(
        active_connection,
    ):
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "loading"

            evidence[
                "transaction_started"
            ] = True

        return (
            loading.load_all_datasets_in_transaction(
                active_connection,
                contract,
            )
        )

    try:
        outcome = (
            rerun.execute_rerun_aware_batch(
                connection=connection,
                batch_id=
                    resolved_batch_id,
                fingerprint=
                    fingerprint,
                pre_write_check=
                    pre_write_check,
                verify_existing_state=
                    verify_existing_state,
                work=
                    work,
            )
        )

    finally:
        connection.close()

    print()

    if (
        outcome["action"]
        == rerun.ACTION_SKIP
    ):
        if evidence is not None:
            evidence[
                "run_status"
            ] = (
                run_history.STATUS_SKIPPED
            )

            evidence[
                "transaction_outcome"
            ] = None

            evidence[
                "current_stage"
            ] = "completed"

        print(
            "Part 9F rerun decision: SKIP"
        )

        print(
            "The same successful "
            "batch and fingerprint "
            "were already processed."
        )

        print(
            "Existing target counts "
            "were reconciled; "
            "no target writes "
            "were performed."
        )

        logger.info(
            "Full-load rerun "
            "decision=SKIP "
            "business_writes=0"
        )

        return outcome

    summary = (
        outcome["result"]
    )

    # Returning ACTION_PROCESS means db.run_atomic already committed
    # the business transaction successfully.
    if evidence is not None:
        evidence[
            "transaction_outcome"
        ] = (
            run_history.TRANSACTION_COMMIT
        )

        evidence[
            "run_status"
        ] = (
            run_history.STATUS_SUCCESS
        )

        evidence[
            "datasets_processed"
        ] = len(
            summary["results"]
        )

        evidence[
            "raw_records_scanned"
        ] = (
            summary[
                "raw_rows"
            ]
        )

        evidence[
            "duplicates_skipped"
        ] = (
            summary[
                "duplicates_skipped"
            ]
        )

        evidence[
            "rows_loaded"
        ] = (
            summary[
                "inserted_rows"
            ]
        )

        evidence[
            "target_tables_reconciled"
        ] = len(
            summary[
                "target_counts"
            ]
        )

        evidence[
            "current_stage"
        ] = "completed"

    print(
        "Part 9D full load: "
        "COMMIT complete"
    )

    print(
        f"Raw records processed: "
        f"{summary['raw_rows']}"
    )

    print(
        "Exact duplicate deliveries "
        "skipped: "
        f"{summary['duplicates_skipped']}"
    )

    print(
        "Rows loaded to PostgreSQL: "
        f"{summary['inserted_rows']}"
    )

    print(
        "Target tables reconciled: "
        f"{len(summary['target_counts'])}/49"
    )

    print(
        "Part 9D basic "
        "reconciliation: PASS"
    )

    print(
        "Part 9F batch state: SUCCESS"
    )

    logger.info(
        "Full-load completed "
        "transaction=COMMIT "
        "datasets=%s raw=%s "
        "duplicates_skipped=%s "
        "rows_loaded=%s",
        len(
            summary["results"]
        ),
        summary["raw_rows"],
        summary[
            "duplicates_skipped"
        ],
        summary[
            "inserted_rows"
        ],
    )

    return outcome


def _execute_mode(
    args,
    *,
    evidence=None,
):
    print_startup_configuration(
        args.mode
    )

    logger.info(
        "Pipeline mode execution started"
    )

    if args.mode == "dq":
        if evidence is None:
            return run_dq_mode()

        evidence[
            "current_stage"
        ] = "dq"

        (
            exit_code,
            summary,
        ) = (
            run_dq_mode(
                capture_summary=True
            )
        )

        evidence[
            "dq_rules_executed"
        ] = (
            summary[
                "rules_executed"
            ]
        )

        evidence[
            "dq_pass_count"
        ] = (
            summary[
                "pass_count"
            ]
        )

        evidence[
            "dq_fail_count"
        ] = (
            summary[
                "fail_count"
            ]
        )

        evidence[
            "dq_total_violations"
        ] = (
            summary[
                "total_violations"
            ]
        )

        evidence[
            "dq_status"
        ] = (
            "PASS"
            if exit_code == 0
            else "FAIL"
        )

        # A DQ FAIL is a valid framework execution whose data-quality
        # outcome is FAIL. Framework/SQL exceptions are handled separately.
        evidence[
            "run_status"
        ] = (
            run_history.STATUS_SUCCESS
        )

        evidence[
            "current_stage"
        ] = "completed"

        return exit_code

    if evidence is not None:
        evidence[
            "current_stage"
        ] = "startup_metadata"

    contract = (
        load_and_validate_startup_metadata()
    )

    if evidence is not None:
        evidence[
            "datasets_expected"
        ] = (
            contract[
                "dataset_count"
            ]
        )

    if args.mode == "validate":
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "validation"

        summary = (
            run_validation_mode(
                contract
            )
        )

        _apply_validation_evidence(
            evidence,
            summary,
        )

    elif args.mode == "plan-check":
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "load_plan"

        run_plan_check(
            contract
        )

    elif (
        args.mode
        == "transform-check"
    ):
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "load_plan"

        run_plan_check(
            contract
        )

        if evidence is not None:
            evidence[
                "current_stage"
            ] = "transformation"

        run_transform_check()

    elif (
        args.mode
        == "target-check"
    ):
        if evidence is not None:
            evidence[
                "current_stage"
            ] = "load_plan"

        run_plan_check(
            contract
        )

        if evidence is not None:
            evidence[
                "current_stage"
            ] = "target_check"

        run_target_check()

    elif args.mode == "full-load":
        run_full_load(
            contract,
            batch_id=
                args.batch_id,
            evidence=
                evidence,
        )

        return 0

    else:
        raise RuntimeError(
            f"Unsupported mode: "
            f"{args.mode}"
        )

    if evidence is not None:
        evidence[
            "run_status"
        ] = (
            run_history.STATUS_SUCCESS
        )

        evidence[
            "current_stage"
        ] = "completed"

    return 0


def main(
    argv=None,
):
    """Test-friendly dispatcher preserving the verified Part 9F CLI contract."""
    args = parse_args(
        argv
    )

    exit_code = (
        _execute_mode(
            args,
            evidence=None,
        )
    )

    if args.mode == "dq":
        raise SystemExit(
            exit_code
        )

    # Preserve the previous non-DQ main() behaviour.
    return None


def _finalize_run_from_evidence(
    connection,
    evidence,
    *,
    status,
    finished_at,
    duration_ms,
    failure_stage=None,
    error_type=None,
    error_message=None,
):
    run_history.finalize_run(
        connection,

        run_id=
            evidence["run_id"],

        status=
            status,

        finished_at=
            finished_at,

        duration_ms=
            duration_ms,

        batch_id=
            evidence.get(
                "batch_id"
            ),

        fingerprint=
            evidence.get(
                "fingerprint"
            ),

        validation_status=
            evidence.get(
                "validation_status"
            ),

        datasets_expected=
            evidence.get(
                "datasets_expected"
            ),

        datasets_processed=
            evidence.get(
                "datasets_processed"
            ),

        raw_records_scanned=
            evidence.get(
                "raw_records_scanned"
            ),

        duplicates_skipped=
            evidence.get(
                "duplicates_skipped"
            ),

        rows_loaded=
            evidence.get(
                "rows_loaded"
            ),

        target_tables_reconciled=
            evidence.get(
                "target_tables_reconciled"
            ),

        transaction_outcome=
            evidence.get(
                "transaction_outcome"
            ),

        dq_rules_executed=
            evidence.get(
                "dq_rules_executed"
            ),

        dq_pass_count=
            evidence.get(
                "dq_pass_count"
            ),

        dq_fail_count=
            evidence.get(
                "dq_fail_count"
            ),

        dq_total_violations=
            evidence.get(
                "dq_total_violations"
            ),

        dq_status=
            evidence.get(
                "dq_status"
            ),

        failure_stage=
            failure_stage,

        error_type=
            error_type,

        error_message=
            error_message,
    )


def _print_run_summary(
    evidence,
    *,
    status,
    duration_ms,
    failure_stage=None,
    error_type=None,
):
    print()

    print(
        "Run Summary"
    )

    print(
        "-----------"
    )

    print(
        f"Run ID: "
        f"{evidence['run_id']}"
    )

    print(
        f"Mode: "
        f"{evidence['mode']}"
    )

    print(
        "Batch ID: "
        f"{evidence.get('batch_id') or 'N/A'}"
    )

    print(
        f"Status: "
        f"{status}"
    )

    print(
        "Transaction: "
        f"{evidence.get('transaction_outcome') or 'N/A'}"
    )

    if (
        evidence.get(
            "datasets_processed"
        )
        is not None
    ):
        print(
            "Datasets processed: "
            f"{evidence['datasets_processed']}"
        )

    if (
        evidence.get(
            "raw_records_scanned"
        )
        is not None
    ):
        print(
            "Raw records: "
            f"{evidence['raw_records_scanned']}"
        )

    if (
        evidence.get(
            "duplicates_skipped"
        )
        is not None
    ):
        print(
            "Duplicates skipped: "
            f"{evidence['duplicates_skipped']}"
        )

    if (
        evidence.get(
            "rows_loaded"
        )
        is not None
    ):
        print(
            "Rows loaded: "
            f"{evidence['rows_loaded']}"
        )

    if (
        evidence.get(
            "dq_status"
        )
        is not None
    ):
        print(
            f"DQ: "
            f"{evidence['dq_status']}"
        )

    if failure_stage is not None:
        print(
            f"Failure stage: "
            f"{failure_stage}"
        )

    if error_type is not None:
        print(
            f"Error type: "
            f"{error_type}"
        )

    print(
        f"Duration: "
        f"{duration_ms / 1000:.3f}s"
    )


def run_with_evidence(
    argv=None,
):
    """Run one CLI invocation with durable Part 9G logs and run history."""
    args = parse_args(
        argv
    )

    run_id = (
        run_history.new_run_id()
    )

    started_at = (
        run_history.utc_now()
    )

    started_monotonic = (
        time.perf_counter()
    )

    log_path = (
        logging_config.configure_logging()
    )

    logging_config.set_log_context(
        run_id=run_id,
        mode=args.mode,
    )

    evidence = {
        "run_id":
            run_id,

        "mode":
            args.mode,

        "current_stage":
            "startup",

        "transaction_started":
            False,
    }

    metadata_connection = None
    history_created = False
    exit_code = 0

    try:
        logger.info(
            "Run started "
            "persistent_log=%s",
            log_path,
        )

        metadata_connection = (
            db.open_connection(
                autocommit=True
            )
        )

        run_history.ensure_run_history_table(
            metadata_connection
        )

        run_history.create_run(
            metadata_connection,
            run_id=run_id,
            mode=args.mode,
            started_at=started_at,
        )

        history_created = True

        exit_code = (
            _execute_mode(
                args,
                evidence=evidence,
            )
        )

        finished_at = (
            run_history.utc_now()
        )

        duration_ms = round(
            (
                time.perf_counter()
                - started_monotonic
            )
            * 1000
        )

        status = (
            evidence.get(
                "run_status",
                run_history.STATUS_SUCCESS,
            )
        )

        _finalize_run_from_evidence(
            metadata_connection,
            evidence,
            status=status,
            finished_at=
                finished_at,
            duration_ms=
                duration_ms,
        )

        logger.info(
            "Run completed "
            "status=%s "
            "transaction=%s "
            "duration_ms=%s",
            status,
            (
                evidence.get(
                    "transaction_outcome"
                )
                or "N/A"
            ),
            duration_ms,
        )

        _print_run_summary(
            evidence,
            status=status,
            duration_ms=
                duration_ms,
        )

    except Exception as error:
        finished_at = (
            run_history.utc_now()
        )

        duration_ms = round(
            (
                time.perf_counter()
                - started_monotonic
            )
            * 1000
        )

        if (
            evidence.get(
                "transaction_started"
            )
            and evidence.get(
                "transaction_outcome"
            )
            is None
        ):
            evidence[
                "transaction_outcome"
            ] = (
                run_history.TRANSACTION_ROLLBACK
            )

        failure_stage = (
            evidence.get(
                "current_stage",
                "unknown",
            )
        )

        if (
            failure_stage
            == "validation"
        ):
            evidence[
                "validation_status"
            ] = "FAIL"

        error_type = (
            type(error).__name__
        )

        safe_error_message = (
            logging_config.redact_text(
                error
            )
        )

        if history_created:
            try:
                _finalize_run_from_evidence(
                    metadata_connection,
                    evidence,
                    status=
                        run_history.STATUS_FAILED,
                    finished_at=
                        finished_at,
                    duration_ms=
                        duration_ms,
                    failure_stage=
                        failure_stage,
                    error_type=
                        error_type,
                    error_message=
                        safe_error_message,
                )

            except Exception as history_error:
                logger.error(
                    "Run-history failure "
                    "finalization also "
                    "failed: %s",
                    logging_config.redact_text(
                        history_error
                    ),
                )

        logger.exception(
            "Run failed "
            "stage=%s "
            "error_type=%s "
            "error=%s "
            "transaction=%s",
            failure_stage,
            error_type,
            safe_error_message,
            (
                evidence.get(
                    "transaction_outcome"
                )
                or "N/A"
            ),
        )

        _print_run_summary(
            evidence,
            status=
                run_history.STATUS_FAILED,
            duration_ms=
                duration_ms,
            failure_stage=
                failure_stage,
            error_type=
                error_type,
        )

        raise

    finally:
        if (
            metadata_connection
            is not None
        ):
            metadata_connection.close()

        logging_config.clear_log_context()

        logging_config.shutdown_logging()

    if exit_code != 0:
        raise SystemExit(
            exit_code
        )

    return exit_code


if __name__ == "__main__":
    try:
        run_with_evidence()

    except Exception as error:
        print()

        print(
            "Pipeline failed: "
            f"{logging_config.redact_text(error)}"
        )

        raise