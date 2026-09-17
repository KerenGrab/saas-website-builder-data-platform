"""Canonical Part 9D source-to-target load plan.

This module contains only declarative metadata and self-checks.  It does not
open source files, transform records, or write to PostgreSQL.
"""

EXPECTED_DATASET_COUNT = 49
EXPECTED_REFERENCE_RAW_ROWS = 2_903_577
EXPECTED_REFERENCE_TARGET_ROWS = 2_899_939

# Part 8 execution groups are reused only as dependency-aware execution order.
# They are NOT transaction boundaries.  Part 9D uses one transaction for all
# five groups.
EXECUTION_GROUPS = (
    (1, 2, 17, 43),
    tuple(range(3, 17)) + tuple(range(18, 31)) + tuple(range(44, 50)),
    (32, 33, 35, 36, 37, 39, 41),
    (31, 34, 40, 42),
    (38,),
)

# Exact duplicate deliveries preserved in Raw Truth.  The target keeps one
# physical event identity after verifying that repeated event_id payloads are
# identical.
EXPECTED_EXACT_DUPLICATES = {
    31: 900,
    34: 480,
    38: 2_200,
    40: 3,
    42: 55,
}

# The two canonical projection cases.  These fields exist in the source but
# are intentionally not persisted in the normalized target table.
DROP_FIELDS = {
    8: ("user_id", "account_id"),
    36: ("website_id",),
}

# number: (canonical source dataset name, target table, mapping type,
#          execution prerequisites expressed as dataset numbers)
CANONICAL_DATASETS = {
    1: ("account", "account", "direct", ()),
    2: ("saas_user", "saas_user", "direct", ()),
    3: (
        "user_account_membership",
        "user_account_membership",
        "direct",
        (1, 2),
    ),
    4: (
        "membership_period",
        "user_account_membership_period",
        "rename",
        (3,),
    ),
    5: (
        "role_assignment_period",
        "user_account_role_assignment_period",
        "rename",
        (3,),
    ),
    6: (
        "account_lifecycle_period",
        "account_lifecycle_period",
        "direct",
        (1,),
    ),
    7: (
        "account_lifecycle_events",
        "account_lifecycle_event",
        "rename",
        (1,),
    ),
    8: (
        "membership_lifecycle_events",
        "user_account_membership_event",
        "projection_rename",
        (3,),
    ),
    9: ("website", "website", "direct", (1,)),
    10: ("page", "page", "direct", (9,)),
    11: ("content_item", "content_item", "direct", (10,)),
    12: (
        "page_access_period",
        "page_access_period",
        "direct",
        (10,),
    ),
    13: (
        "content_item_access_period",
        "content_item_access_period",
        "direct",
        (11,),
    ),
    14: (
        "website_lifecycle_events",
        "website_lifecycle_event",
        "rename",
        (9,),
    ),
    15: (
        "website_live_period",
        "website_live_period",
        "direct",
        (9,),
    ),
    16: (
        "website_address_history",
        "website_address_period",
        "rename",
        (9,),
    ),
    17: ("feature", "feature", "direct", ()),
    18: (
        "plan_feature_entitlement_history",
        "plan_feature_entitlement_period",
        "rename",
        (17, 43),
    ),
    19: (
        "website_feature_enablement_period",
        "website_feature_enablement_period",
        "direct",
        (9, 17),
    ),
    20: (
        "feature_enablement_lifecycle_events",
        "feature_enablement_lifecycle_event",
        "rename",
        (9, 17),
    ),
    21: ("website_member", "website_member", "direct", (9,)),
    22: (
        "membership_invitation",
        "membership_invitation",
        "direct",
        (9,),
    ),
    23: (
        "invitation_outcome_events",
        "invitation_outcome_event",
        "rename",
        (22,),
    ),
    24: (
        "member_registration_success_events",
        "member_registration_success_event",
        "rename",
        (9, 21, 22),
    ),
    25: (
        "member_state_history",
        "member_state_period",
        "rename",
        (21,),
    ),
    26: (
        "member_profile_update_events",
        "member_profile_update_event",
        "rename",
        (21,),
    ),
    27: ("comment", "comment", "direct", (10, 21)),
    28: (
        "comment_lifecycle_events",
        "comment_lifecycle_event",
        "rename",
        (27,),
    ),
    29: ("rating", "rating", "direct", (10, 21)),
    30: (
        "rating_lifecycle_events",
        "rating_lifecycle_event",
        "rename",
        (29,),
    ),
    31: (
        "product_behaviour_events",
        "product_behaviour_event",
        "jsonl_dedup_rename",
        (1, 2, 9, 17),
    ),
    32: ("visitor", "visitor", "direct", (9,)),
    33: (
        "audience_session",
        "audience_session",
        "direct",
        (9, 32),
    ),
    34: (
        "session_lifecycle_events",
        "session_lifecycle_event",
        "jsonl_dedup_rename",
        (33,),
    ),
    35: (
        "session_traffic_attribution",
        "session_traffic_attribution",
        "direct",
        (33,),
    ),
    36: (
        "visitor_member_linkage",
        "visitor_member_linkage",
        "projection",
        (21, 32),
    ),
    37: (
        "session_member_attribution",
        "session_member_attribution",
        "direct",
        (21, 33),
    ),
    38: (
        "audience_interaction_events",
        "audience_interaction_event",
        "jsonl_dedup_rename",
        (10, 11, 33),
    ),
    39: (
        "signup_journey_context",
        "signup_journey_context",
        "direct",
        (1,),
    ),
    40: (
        "signup_journey_events",
        "signup_journey_event",
        "jsonl_dedup_rename",
        (39,),
    ),
    41: (
        "acquisition_source_attribution",
        "acquisition_source_attribution",
        "direct",
        (39,),
    ),
    42: (
        "membership_behaviour_events",
        "membership_behaviour_event",
        "jsonl_dedup_rename",
        (9, 21),
    ),
    43: ("plan_catalog", "plan_catalog", "direct", ()),
    44: (
        "subscription_plan_period",
        "subscription_plan_period",
        "direct",
        (1, 43),
    ),

    # #45 has an execution prerequisite on #44 because its business rule is
    # containment in a paid subscription period, even though its physical FK
    # is to account rather than directly to #44.
    45: (
        "billing_cycle_period",
        "billing_cycle_period",
        "direct",
        (1, 44),
    ),
    46: (
        "subscription_lifecycle_events",
        "subscription_lifecycle_event",
        "rename",
        (1, 43),
    ),
    47: (
        "payment_refund_activity_events",
        "payment_refund_activity_event",
        "rename",
        (1,),
    ),
    48: (
        "support_request",
        "support_request",
        "direct",
        (1, 2, 9),
    ),
    49: (
        "support_lifecycle_events",
        "support_lifecycle_event",
        "rename",
        (48,),
    ),
}


def iter_dataset_numbers_in_load_order():
    """Yield all 49 dataset numbers in canonical execution order."""
    for group in EXECUTION_GROUPS:
        yield from group


def get_load_spec(dataset_number):
    """Return declarative load metadata for one canonical dataset."""
    try:
        source_dataset, target_table, mapping_type, dependencies = (
            CANONICAL_DATASETS[dataset_number]
        )
    except KeyError as error:
        raise ValueError(
            f"No canonical load mapping exists for Dataset #{dataset_number}."
        ) from error

    return {
        "number": dataset_number,
        "source_dataset": source_dataset,
        "target_table": target_table,
        "mapping_type": mapping_type,
        "dependencies": dependencies,
        "drop_fields": DROP_FIELDS.get(dataset_number, ()),
        "deduplicate_by_event_id":
            dataset_number in EXPECTED_EXACT_DUPLICATES,
        "expected_exact_duplicates":
            EXPECTED_EXACT_DUPLICATES.get(dataset_number, 0),
    }


def get_target_tables_in_load_order():
    """Return target table names in the exact Part 9D execution order."""
    return [
        get_load_spec(number)["target_table"]
        for number in iter_dataset_numbers_in_load_order()
    ]


def expected_target_rows(dataset_metadata):
    """Return expected target rows for the frozen reference input."""
    dataset_number = dataset_metadata["number"]

    return (
        dataset_metadata["rows"]
        - EXPECTED_EXACT_DUPLICATES.get(dataset_number, 0)
    )


def validate_load_plan(contract):
    """Fail fast if the declarative plan drifts from the frozen contract."""
    expected_numbers = set(
        range(1, EXPECTED_DATASET_COUNT + 1)
    )

    plan_numbers = set(CANONICAL_DATASETS)

    if plan_numbers != expected_numbers:
        missing = sorted(
            expected_numbers - plan_numbers
        )

        extra = sorted(
            plan_numbers - expected_numbers
        )

        raise ValueError(
            "Canonical load plan must cover Datasets #1-#49 exactly once. "
            f"Missing={missing}, extra={extra}."
        )

    ordered_numbers = list(
        iter_dataset_numbers_in_load_order()
    )

    if len(ordered_numbers) != EXPECTED_DATASET_COUNT:
        raise ValueError(
            "Execution groups must contain exactly 49 dataset entries."
        )

    if set(ordered_numbers) != expected_numbers:
        raise ValueError(
            "Execution groups must cover every Dataset #1-#49 exactly once."
        )

    if len(ordered_numbers) != len(set(ordered_numbers)):
        raise ValueError(
            "Execution groups contain a duplicate dataset number."
        )

    target_tables = get_target_tables_in_load_order()

    if len(target_tables) != len(set(target_tables)):
        raise ValueError(
            "Two source datasets map to the same target table."
        )

    contract_by_number = {
        dataset["number"]: dataset
        for dataset in contract["datasets"]
    }

    if set(contract_by_number) != expected_numbers:
        raise ValueError(
            "Frozen input contract does not contain Datasets #1-#49."
        )

    raw_total = 0
    expected_target_total = 0

    for dataset_number in range(1, 50):

        dataset_metadata = contract_by_number[
            dataset_number
        ]

        spec = get_load_spec(dataset_number)

        if (
            dataset_metadata["dataset"]
            != spec["source_dataset"]
        ):
            raise ValueError(
                f"Dataset #{dataset_number} name mismatch: "
                f"contract has '{dataset_metadata['dataset']}', "
                f"load plan expects '{spec['source_dataset']}'."
            )

        should_be_jsonl = (
            dataset_number
            in EXPECTED_EXACT_DUPLICATES
        )

        if (
            should_be_jsonl
            and dataset_metadata["format"] != "jsonl"
        ):
            raise ValueError(
                f"Dataset #{dataset_number} must be JSONL "
                "for canonical event duplicate handling."
            )

        if (
            not should_be_jsonl
            and dataset_metadata["format"] == "jsonl"
        ):
            raise ValueError(
                f"Unexpected JSONL Dataset #{dataset_number}; "
                "update the canonical load plan before loading."
            )

        duplicates = spec[
            "expected_exact_duplicates"
        ]

        if duplicates >= dataset_metadata["rows"]:
            raise ValueError(
                f"Dataset #{dataset_number} has an invalid "
                "expected duplicate count."
            )

        raw_total += dataset_metadata["rows"]

        expected_target_total += (
            expected_target_rows(
                dataset_metadata
            )
        )

    if raw_total != EXPECTED_REFERENCE_RAW_ROWS:
        raise ValueError(
            "Frozen reference raw-row total mismatch. "
            f"Expected {EXPECTED_REFERENCE_RAW_ROWS}, "
            f"contract has {raw_total}."
        )

    if (
        expected_target_total
        != EXPECTED_REFERENCE_TARGET_ROWS
    ):
        raise ValueError(
            "Frozen reference target-row total mismatch. "
            f"Expected {EXPECTED_REFERENCE_TARGET_ROWS}, "
            f"derived {expected_target_total}."
        )

    order_position = {
        dataset_number: position
        for position, dataset_number
        in enumerate(ordered_numbers)
    }

    for dataset_number in ordered_numbers:

        dependencies = get_load_spec(
            dataset_number
        )["dependencies"]

        for dependency_number in dependencies:

            if dependency_number not in expected_numbers:
                raise ValueError(
                    f"Dataset #{dataset_number} references "
                    f"unknown dependency #{dependency_number}."
                )

            if (
                order_position[dependency_number]
                >= order_position[dataset_number]
            ):
                raise ValueError(
                    f"Dependency order error: Dataset "
                    f"#{dependency_number} must load before "
                    f"Dataset #{dataset_number}."
                )

    if set(DROP_FIELDS) != {8, 36}:
        raise ValueError(
            "Only canonical projection cases #8 and #36 are allowed."
        )

    if (
        set(EXPECTED_EXACT_DUPLICATES)
        != {31, 34, 38, 40, 42}
    ):
        raise ValueError(
            "Canonical JSONL duplicate-aware set must be "
            "#31/#34/#38/#40/#42."
        )

    return {
        "datasets": EXPECTED_DATASET_COUNT,
        "execution_groups":
            len(EXECUTION_GROUPS),
        "raw_rows":
            raw_total,
        "expected_target_rows":
            expected_target_total,
        "projection_cases":
            len(DROP_FIELDS),
        "duplicate_aware_streams":
            len(EXPECTED_EXACT_DUPLICATES),
        "expected_exact_duplicates":
            sum(
                EXPECTED_EXACT_DUPLICATES.values()
            ),
    }