"""
Source-data ingestion utilities for the SaaS data pipeline.

This module is responsible for opening canonical source files
and yielding their raw records one at a time.

The pipeline supports the two source formats used by the frozen
canonical input package:

- CSV
- JSONL

The ingestion layer uses generators so that large source files
do not need to be loaded completely into memory.

This module does NOT:
- transform source data;
- deduplicate events;
- validate cross-dataset relationships;
- load data into PostgreSQL;
- manage transactions.
"""

import csv
import json

from pipeline import paths


def get_source_path(dataset_metadata):
    """
    Build the full local path for one canonical source dataset.

    Args:
        dataset_metadata (dict):
            Metadata for one dataset from the final input contract.

    Returns:
        Path:
            Full filesystem path to the source file.

    Raises:
        RuntimeError:
            If SOURCE_ROOT is not configured.

        ValueError:
            If the dataset does not define a source path.

        FileNotFoundError:
            If the declared source file does not exist.
    """

    if paths.SOURCE_ROOT is None:
        raise RuntimeError(
            "Cannot resolve source file because "
            "SOURCE_ROOT is not configured."
        )

    relative_path = dataset_metadata.get("path")

    if not relative_path:
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "does not define a source path."
        )

    source_path = paths.SOURCE_ROOT / relative_path

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Source file not found: {source_path}"
        )

    return source_path


def iter_csv_dataset(dataset_metadata):
    """
    Yield records from one canonical CSV dataset.

    Unlike the earlier implementation, this function does NOT create
    a list containing the complete source file.

    Each CSV record is yielded individually as a dictionary.

    Args:
        dataset_metadata (dict):
            Metadata for one dataset.

    Yields:
        dict:
            One CSV record at a time.

    Raises:
        ValueError:
            If the dataset is not declared as CSV.
    """

    if dataset_metadata.get("format") != "csv":
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "is not declared as CSV."
        )

    source_path = get_source_path(dataset_metadata)

    with source_path.open(
        "r",
        encoding="utf-8",
        newline="",
    ) as source_file:

        reader = csv.DictReader(source_file)

        for record in reader:
            yield record


def iter_jsonl_dataset(dataset_metadata):
    """
    Yield records from one canonical JSONL dataset.

    JSONL stores one independent JSON object on every line.

    The file is read line by line so that the complete event stream
    does not need to be kept in memory.

    Args:
        dataset_metadata (dict):
            Metadata for one dataset.

    Yields:
        dict:
            One parsed JSON object at a time.

    Raises:
        ValueError:
            If the dataset is not declared as JSONL,
            if a line contains invalid JSON,
            or if a JSON line is not an object.
    """

    if dataset_metadata.get("format") != "jsonl":
        raise ValueError(
            f"Dataset #{dataset_metadata['number']} "
            "is not declared as JSONL."
        )

    source_path = get_source_path(dataset_metadata)

    with source_path.open(
        "r",
        encoding="utf-8",
    ) as source_file:

        for line_number, line in enumerate(
            source_file,
            start=1,
        ):
            stripped_line = line.strip()

            # Completely empty lines are ignored.
            if not stripped_line:
                continue

            try:
                record = json.loads(stripped_line)

            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON in Dataset "
                    f"#{dataset_metadata['number']} "
                    f"at line {line_number}: {error}"
                ) from error

            if not isinstance(record, dict):
                raise ValueError(
                    f"Dataset #{dataset_metadata['number']} "
                    f"contains a non-object JSON value "
                    f"at line {line_number}."
                )

            yield record


def iter_dataset_records(dataset_metadata):
    """
    Yield records from one canonical dataset using the correct parser.

    The dataset format determines which ingestion function is used:

        csv
            -> iter_csv_dataset()

        jsonl
            -> iter_jsonl_dataset()

    Args:
        dataset_metadata (dict):
            Metadata for one dataset.

    Yields:
        dict:
            One source record at a time.

    Raises:
        ValueError:
            If the declared source format is unsupported.
    """

    dataset_format = dataset_metadata.get("format")

    if dataset_format == "csv":
        yield from iter_csv_dataset(dataset_metadata)
        return

    if dataset_format == "jsonl":
        yield from iter_jsonl_dataset(dataset_metadata)
        return

    raise ValueError(
        f"Unsupported format for Dataset "
        f"#{dataset_metadata['number']}: "
        f"{dataset_format}"
    )