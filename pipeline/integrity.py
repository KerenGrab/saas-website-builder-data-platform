"""
Frozen-input integrity utilities for the SaaS data pipeline.

This module verifies that the local canonical source files are the
exact files described by the frozen Part 9 input contract.

Two reference checks are performed:

1. Reference row count
   - the number of parsed records must match the frozen contract.

2. SHA256
   - the raw file bytes must match the exact SHA256 stored
     in the frozen contract.

Important:
These checks apply to the frozen canonical reference package used
by this project.

They are NOT general rules requiring future batches to have the
same number of rows.
"""

import hashlib

from pipeline import ingestion


def calculate_sha256(dataset_metadata):
    """
    Calculate the SHA256 hash of one canonical source file.

    The file is opened in binary mode so that the hash represents
    the exact raw bytes on disk.

    The file is read in chunks instead of loading the entire file
    into memory.

    Args:
        dataset_metadata (dict):
            Metadata for one dataset from the final input contract.

    Returns:
        str:
            Lowercase hexadecimal SHA256 digest.
    """

    source_path = ingestion.get_source_path(
        dataset_metadata
    )

    sha256 = hashlib.sha256()

    # Read 1 MiB at a time.
    chunk_size = 1024 * 1024

    with source_path.open("rb") as source_file:

        while True:
            chunk = source_file.read(chunk_size)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def validate_frozen_reference_integrity(
    dataset_metadata,
    actual_row_count,
):
    """
    Validate one dataset against its frozen reference metadata.

    The function checks:

    - actual parsed row count == contract row count;
    - actual file SHA256 == contract SHA256.

    Args:
        dataset_metadata (dict):
            Metadata for one canonical dataset.

        actual_row_count (int):
            Number of source records observed during streaming
            structural validation.

    Returns:
        str:
            The successfully verified SHA256 digest.

    Raises:
        ValueError:
            If reference metadata is missing or invalid,
            if the row count differs,
            or if the SHA256 differs.
    """

    dataset_number = dataset_metadata["number"]

    # ------------------------------------------------------------------
    # Reference row-count metadata
    # ------------------------------------------------------------------

    expected_row_count = dataset_metadata.get("rows")

    if not isinstance(expected_row_count, int):
        raise ValueError(
            f"Dataset #{dataset_number} "
            "does not define a valid frozen reference row count."
        )

    if actual_row_count != expected_row_count:
        raise ValueError(
            f"Dataset #{dataset_number} row-count mismatch. "
            f"Expected {expected_row_count}, "
            f"but found {actual_row_count}."
        )

    # ------------------------------------------------------------------
    # Reference SHA256 metadata
    # ------------------------------------------------------------------

    expected_sha256 = dataset_metadata.get("sha256")

    if not isinstance(expected_sha256, str):
        raise ValueError(
            f"Dataset #{dataset_number} "
            "does not define a valid SHA256 value."
        )

    expected_sha256 = expected_sha256.strip().lower()

    if len(expected_sha256) != 64:
        raise ValueError(
            f"Dataset #{dataset_number} "
            "contains an invalid SHA256 digest in the contract."
        )

    # Calculate the hash from the exact raw bytes currently on disk.
    actual_sha256 = calculate_sha256(
        dataset_metadata
    )

    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"Dataset #{dataset_number} SHA256 mismatch. "
            f"Expected {expected_sha256}, "
            f"but found {actual_sha256}."
        )

    return actual_sha256