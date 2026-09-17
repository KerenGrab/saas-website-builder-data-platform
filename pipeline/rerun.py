"""Minimal batch identity, fingerprint, and rerun state for Part 9F.

This module intentionally stores only correctness state required for safe
reruns.  It is not a Part 9G logging or run-history subsystem.
"""

import hashlib
import json

from psycopg import sql

from pipeline import db


PIPELINE_META_SCHEMA = "pipeline_meta"
BATCH_STATE_TABLE = "batch_state"

STATUS_PROCESSING = "PROCESSING"
STATUS_FAILED = "FAILED"
STATUS_SUCCESS = "SUCCESS"

ACTION_PROCESS = "PROCESS"
ACTION_SKIP = "SKIP"


class BatchIdentityConflictError(RuntimeError):
    """Raised when one batch_id is reused for different content."""


class BatchInProgressError(RuntimeError):
    """Raised when the same batch is already marked PROCESSING."""


def resolve_batch_id(contract, explicit_batch_id=None):
    """Return the logical batch identifier used for rerun decisions.

    An explicit CLI batch id wins.  For the frozen canonical package, a
    deterministic fallback based on the contract version preserves existing
    command compatibility while still giving the delivery a stable identity.
    """
    if explicit_batch_id is not None:
        batch_id = str(explicit_batch_id).strip()

        if not batch_id:
            raise ValueError(
                "batch_id must contain at least one non-whitespace character."
            )

        return batch_id

    contract_version = str(
        contract.get("contract_version", "")
    ).strip()

    if not contract_version:
        raise ValueError(
            "Cannot derive a default batch_id because contract_version is missing."
        )

    return f"canonical-contract-v{contract_version}"


def calculate_batch_fingerprint(contract):
    """Build a deterministic SHA256 fingerprint from per-file SHA256 values.

    The 9C integrity gate already verifies that the bytes on disk match the
    per-file SHA256 values in the frozen contract.  Reusing those verified
    digests avoids rereading the complete multi-gigabyte batch only to derive
    a second batch-level identity.
    """
    datasets = contract.get("datasets")

    if not isinstance(datasets, list) or not datasets:
        raise ValueError(
            "Batch fingerprint requires a non-empty contract datasets list."
        )

    normalized = []
    seen_numbers = set()

    for dataset in datasets:
        dataset_number = dataset.get("number")
        digest = dataset.get("sha256")

        if not isinstance(dataset_number, int):
            raise ValueError(
                "Every dataset used for batch fingerprinting must have an integer number."
            )

        if dataset_number in seen_numbers:
            raise ValueError(
                f"Duplicate Dataset #{dataset_number} in batch fingerprint input."
            )

        if not isinstance(digest, str):
            raise ValueError(
                f"Dataset #{dataset_number} does not define a SHA256 digest."
            )

        digest = digest.strip().lower()

        if (
            len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(
                f"Dataset #{dataset_number} has an invalid SHA256 digest."
            )

        seen_numbers.add(dataset_number)
        normalized.append(
            {
                "number": dataset_number,
                "sha256": digest,
            }
        )

    normalized.sort(key=lambda item: item["number"])

    canonical_json = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return hashlib.sha256(
        canonical_json.encode("utf-8")
    ).hexdigest()


def ensure_batch_state_table(connection):
    """Create the minimal pipeline metadata table if it does not yet exist."""
    if not connection.autocommit:
        raise RuntimeError(
            "Batch-state setup requires a connection opened with autocommit=True."
        )

    create_schema = sql.SQL(
        "CREATE SCHEMA IF NOT EXISTS {}"
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA)
    )

    create_table = sql.SQL(
        """
        CREATE TABLE IF NOT EXISTS {}.{} (
            batch_id TEXT PRIMARY KEY,
            fingerprint CHAR(64) NOT NULL,
            status TEXT NOT NULL
                CHECK (status IN ('PROCESSING', 'FAILED', 'SUCCESS')),
            attempt_count INTEGER NOT NULL
                CHECK (attempt_count >= 1)
        )
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(create_schema)
        cursor.execute(create_table)


def get_batch_state(connection, batch_id):
    """Return persisted correctness state for one batch_id, or None."""
    query = sql.SQL(
        """
        SELECT batch_id, fingerprint, status, attempt_count
        FROM {}.{}
        WHERE batch_id = %s
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(query, (batch_id,))
        row = cursor.fetchone()

    if row is None:
        return None

    return {
        "batch_id": row[0],
        "fingerprint": str(row[1]).strip(),
        "status": row[2],
        "attempt_count": row[3],
    }


def decide_batch_action(existing_state, incoming_fingerprint):
    """Pure decision logic for NEW/FAILED/SUCCESS/PROCESSING batch states."""
    if existing_state is None:
        return ACTION_PROCESS

    existing_fingerprint = existing_state["fingerprint"]

    if existing_fingerprint != incoming_fingerprint:
        raise BatchIdentityConflictError(
            "The same batch_id is already registered with different content."
        )

    status = existing_state["status"]

    if status == STATUS_SUCCESS:
        return ACTION_SKIP

    if status == STATUS_FAILED:
        return ACTION_PROCESS

    if status == STATUS_PROCESSING:
        raise BatchInProgressError(
            "The batch is already marked PROCESSING; refusing a concurrent rerun."
        )

    raise RuntimeError(
        f"Unsupported persisted batch status: {status!r}."
    )


def classify_batch(connection, batch_id, fingerprint):
    """Read persisted state and return PROCESS or SKIP without mutation."""
    state = get_batch_state(connection, batch_id)
    return decide_batch_action(
        state,
        fingerprint,
    )


def start_batch_attempt(connection, batch_id, fingerprint):
    """Atomically register a NEW attempt or reopen a FAILED batch.

    SUCCESS returns SKIP as a race-safe no-op.  Different content or an
    already PROCESSING batch is rejected before target mutation.
    """
    if not connection.autocommit:
        raise RuntimeError(
            "Batch attempt setup requires autocommit=True."
        )

    select_for_update = sql.SQL(
        """
        SELECT batch_id, fingerprint, status, attempt_count
        FROM {}.{}
        WHERE batch_id = %s
        FOR UPDATE
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    insert_state = sql.SQL(
        """
        INSERT INTO {}.{}
            (batch_id, fingerprint, status, attempt_count)
        VALUES (%s, %s, %s, 1)
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    update_retry = sql.SQL(
        """
        UPDATE {}.{}
        SET status = %s,
            attempt_count = attempt_count + 1
        WHERE batch_id = %s
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(select_for_update, (batch_id,))
            row = cursor.fetchone()

            if row is None:
                cursor.execute(
                    insert_state,
                    (
                        batch_id,
                        fingerprint,
                        STATUS_PROCESSING,
                    ),
                )
                return ACTION_PROCESS

            state = {
                "batch_id": row[0],
                "fingerprint": str(row[1]).strip(),
                "status": row[2],
                "attempt_count": row[3],
            }

            action = decide_batch_action(
                state,
                fingerprint,
            )

            if action == ACTION_SKIP:
                return ACTION_SKIP

            cursor.execute(
                update_retry,
                (
                    STATUS_PROCESSING,
                    batch_id,
                ),
            )

    return ACTION_PROCESS


def mark_batch_success_in_transaction(
    connection,
    batch_id,
    fingerprint,
):
    """Mark SUCCESS inside the same transaction as target writes."""
    query = sql.SQL(
        """
        UPDATE {}.{}
        SET status = %s
        WHERE batch_id = %s
          AND fingerprint = %s
          AND status = %s
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    with connection.cursor() as cursor:
        cursor.execute(
            query,
            (
                STATUS_SUCCESS,
                batch_id,
                fingerprint,
                STATUS_PROCESSING,
            ),
        )

        if cursor.rowcount != 1:
            raise RuntimeError(
                "Could not atomically mark the processing batch as SUCCESS."
            )


def mark_batch_failed(connection, batch_id, fingerprint):
    """Persist FAILED after the target transaction has rolled back."""
    if not connection.autocommit:
        raise RuntimeError(
            "FAILED batch-state persistence requires autocommit=True."
        )

    query = sql.SQL(
        """
        UPDATE {}.{}
        SET status = %s
        WHERE batch_id = %s
          AND fingerprint = %s
          AND status = %s
        """
    ).format(
        sql.Identifier(PIPELINE_META_SCHEMA),
        sql.Identifier(BATCH_STATE_TABLE),
    )

    with connection.transaction():
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (
                    STATUS_FAILED,
                    batch_id,
                    fingerprint,
                    STATUS_PROCESSING,
                ),
            )

            if cursor.rowcount != 1:
                raise RuntimeError(
                    "Could not persist FAILED state for the processing batch."
                )


def execute_rerun_aware_batch(
    *,
    connection,
    batch_id,
    fingerprint,
    work,
    pre_write_check=None,
    verify_existing_state=None,
):
    """Execute one batch safely with PROCESS/SKIP/conflict semantics.

    work(connection) runs inside one real PostgreSQL transaction.  The SUCCESS
    metadata update is part of that same transaction.  Any work exception
    rolls back target writes, after which FAILED is persisted separately so a
    retry of the same batch/content is allowed.
    """
    ensure_batch_state_table(connection)

    action = classify_batch(
        connection,
        batch_id,
        fingerprint,
    )

    if action == ACTION_SKIP:
        if verify_existing_state is not None:
            verify_existing_state(connection)

        return {
            "action": ACTION_SKIP,
            "batch_id": batch_id,
            "fingerprint": fingerprint,
            "result": None,
        }

    if pre_write_check is not None:
        pre_write_check(connection)

    start_action = start_batch_attempt(
        connection,
        batch_id,
        fingerprint,
    )

    if start_action == ACTION_SKIP:
        if verify_existing_state is not None:
            verify_existing_state(connection)

        return {
            "action": ACTION_SKIP,
            "batch_id": batch_id,
            "fingerprint": fingerprint,
            "result": None,
        }

    try:
        result = db.run_atomic(
            connection,
            work,
            before_commit=lambda active_connection: (
                mark_batch_success_in_transaction(
                    active_connection,
                    batch_id,
                    fingerprint,
                )
            ),
        )

    except Exception as original_error:
        try:
            mark_batch_failed(
                connection,
                batch_id,
                fingerprint,
            )
        except Exception as state_error:
            raise RuntimeError(
                "Batch work failed and FAILED state could not be persisted."
            ) from state_error

        raise

    return {
        "action": ACTION_PROCESS,
        "batch_id": batch_id,
        "fingerprint": fingerprint,
        "result": result,
    }
