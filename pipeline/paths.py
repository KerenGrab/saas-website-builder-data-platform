"""
Filesystem paths used by the SaaS data pipeline.

This module centralizes the important filesystem locations used by
the pipeline.

The pipeline currently works with:

- PROJECT_ROOT:
  The root directory of the Python project.

- SOURCE_ROOT:
  The root directory of the frozen canonical Part 9 input package.

- INPUT_CONTRACT_PATH:
  The final machine-readable input contract.

- RAW_ROOT:
  The directory containing the 49 canonical raw source files.
"""

from pathlib import Path

from pipeline import config


# ---------------------------------------------------------------------------
# Python project root
# ---------------------------------------------------------------------------

# paths.py is located inside:
#
# saas_data_pipeline/pipeline/paths.py
#
# Therefore parent.parent gives us the root of the Python project.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Canonical source package
# ---------------------------------------------------------------------------

# SOURCE_ROOT comes from the environment variable configured in PyCharm.
#
# It should point to the frozen Part 9 input package.
SOURCE_ROOT = (
    Path(config.SOURCE_ROOT).expanduser().resolve()
    if config.SOURCE_ROOT
    else None
)


# ---------------------------------------------------------------------------
# Final input contract
# ---------------------------------------------------------------------------

# The final machine-readable contract describing the 49 canonical
# source datasets.
INPUT_CONTRACT_PATH = (
    SOURCE_ROOT / "final_pipeline_input_contract.json"
    if SOURCE_ROOT
    else None
)


# ---------------------------------------------------------------------------
# Canonical raw source data
# ---------------------------------------------------------------------------

# Directory containing the final frozen raw source files.
RAW_ROOT = (
    SOURCE_ROOT / "raw"
    if SOURCE_ROOT
    else None
)