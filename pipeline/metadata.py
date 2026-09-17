"""
Metadata utilities for the SaaS data pipeline.

This module is responsible for reading and validating the frozen
Part 9 input contract and providing convenient access to dataset
metadata.

The input contract describes the exact 49 canonical source datasets
used by the pipeline.

At this stage, this module performs only metadata and filesystem
startup checks.

It does NOT yet:
- ingest CSV files;
- parse JSONL event streams;
- validate dataset values;
- transform data;
- load data into PostgreSQL.
"""

import json

from pipeline import paths


def load_input_contract():
    """
    Load and perform basic validation of the final pipeline input contract.

    Returns:
        dict:
            The parsed JSON input contract.

    Raises:
        RuntimeError:
            If SOURCE_ROOT is not configured.

        FileNotFoundError:
            If the final input contract cannot be found.

        ValueError:
            If the contract does not contain the expected structure.
    """

    # ------------------------------------------------------------------
    # Path validation
    # ------------------------------------------------------------------

    if paths.INPUT_CONTRACT_PATH is None:
        raise RuntimeError(
            "Input contract path is unavailable because "
            "SOURCE_ROOT is not configured."
        )

    if not paths.INPUT_CONTRACT_PATH.is_file():
        raise FileNotFoundError(
            f"Input contract file not found: "
            f"{paths.INPUT_CONTRACT_PATH}"
        )

    # ------------------------------------------------------------------
    # JSON loading
    # ------------------------------------------------------------------

    with paths.INPUT_CONTRACT_PATH.open(
        "r",
        encoding="utf-8",
    ) as contract_file:
        contract = json.load(contract_file)

    # ------------------------------------------------------------------
    # Basic contract validation
    # ------------------------------------------------------------------

    required_contract_keys = {
        "contract_version",
        "status",
        "datasets_expected",
        "datasets_generated",
        "dataset_count",
        "datasets",
    }

    missing_keys = required_contract_keys - contract.keys()

    if missing_keys:
        raise ValueError(
            "Input contract is missing required keys: "
            f"{sorted(missing_keys)}"
        )

    if not isinstance(contract["datasets"], list):
        raise ValueError(
            "Input contract field 'datasets' must contain a list."
        )

    # ------------------------------------------------------------------
    # Frozen contract checks
    # ------------------------------------------------------------------

    if contract["status"] != "FROZEN":
        raise ValueError(
            "Input contract status must be 'FROZEN'."
        )

    if contract["datasets_expected"] != 49:
        raise ValueError(
            "Input contract must declare 49 expected datasets."
        )

    if contract["datasets_generated"] != 49:
        raise ValueError(
            "Input contract must declare 49 generated datasets."
        )

    if contract["dataset_count"] != 49:
        raise ValueError(
            "Input contract dataset_count must be 49."
        )

    if len(contract["datasets"]) != 49:
        raise ValueError(
            "Input contract must contain exactly 49 dataset entries."
        )

    # ------------------------------------------------------------------
    # Dataset identity checks
    # ------------------------------------------------------------------

    dataset_numbers = [
        dataset["number"]
        for dataset in contract["datasets"]
    ]

    if sorted(dataset_numbers) != list(range(1, 50)):
        raise ValueError(
            "Dataset numbers must contain every value from 1 to 49 "
            "exactly once."
        )

    dataset_names = [
        dataset["dataset"]
        for dataset in contract["datasets"]
    ]

    if len(dataset_names) != len(set(dataset_names)):
        raise ValueError(
            "Dataset names in the input contract must be unique."
        )

    return contract


def get_dataset_by_number(contract, dataset_number):
    """
    Return metadata for one dataset identified by its canonical number.

    Args:
        contract (dict):
            The parsed final input contract.

        dataset_number (int):
            Canonical dataset number between 1 and 49.

    Returns:
        dict:
            Metadata for the requested dataset.

    Raises:
        ValueError:
            If the dataset number is invalid or cannot be found.
    """

    if not isinstance(dataset_number, int):
        raise ValueError(
            "Dataset number must be an integer."
        )

    if dataset_number < 1 or dataset_number > 49:
        raise ValueError(
            "Dataset number must be between 1 and 49."
        )

    for dataset in contract["datasets"]:
        if dataset["number"] == dataset_number:
            return dataset

    # This should never happen after the contract itself passed validation,
    # but we still fail explicitly instead of returning None silently.
    raise ValueError(
        f"Dataset #{dataset_number} was not found in the input contract."
    )


def validate_source_files(contract):
    """
    Verify that all source files declared in the input contract exist.

    This is only a filesystem availability check.

    The function does NOT open or parse CSV/JSONL contents.

    Args:
        contract (dict):
            The parsed final input contract.

    Returns:
        int:
            Number of canonical source files successfully located.

    Raises:
        RuntimeError:
            If SOURCE_ROOT is unavailable.

        FileNotFoundError:
            If one or more declared source files cannot be found.

        ValueError:
            If a dataset entry does not define a valid path.
    """

    if paths.SOURCE_ROOT is None:
        raise RuntimeError(
            "Cannot validate source files because "
            "SOURCE_ROOT is not configured."
        )

    missing_files = []

    for dataset in contract["datasets"]:
        relative_path = dataset.get("path")

        if not relative_path:
            raise ValueError(
                f"Dataset #{dataset['number']} "
                "does not define a source path."
            )

        source_path = paths.SOURCE_ROOT / relative_path

        if not source_path.is_file():
            missing_files.append(
                f"Dataset #{dataset['number']}: {source_path}"
            )

    if missing_files:
        raise FileNotFoundError(
            "One or more canonical source files are missing:\n"
            + "\n".join(missing_files)
        )

    return len(contract["datasets"])