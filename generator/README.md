# Synthetic Data Generator

This directory contains the synthetic-data generation and validation code used for the Website Builder SaaS data-platform project.

The generator produces the complete 49-dataset source landscape across four source families: Core Product, Event Tracking, Billing & Payment, and Support Ticketing.

## Contents

- `generate_raw_data.py` — generates the synthetic raw-source package.
- `validate_raw_data.py` — validates structural, temporal, and business-rule consistency.
- `requirements.txt` — generator-specific Python dependencies.

## Tested Environment

The repository-maintained generator was verified with:

- Python 3.11
- NumPy 2.4.6
- pandas 3.0.6

Install the generator dependencies with:

`python -m pip install -r generator/requirements.txt`

## Generate Data

Always provide a dedicated output directory.

Example:

`python generator/generate_raw_data.py --scale 1.0 --out C:\temp\saas_generated_data`

The generator writes the generated raw datasets together with `manifest.json` and `generation_summary.json`.

The canonical seed embedded in the generator is `20260821`.

The modeled source period is `2024-01-01` through `2025-12-31`.

## Validate a Generated Package

The validator expects to run beside the generated `manifest.json` file and `raw` directory.

Example package structure:

- `validate_raw_data.py`
- `manifest.json`
- `raw/`

Example:

`Copy-Item generator\validate_raw_data.py C:\temp\saas_generated_data\validate_raw_data.py`

Then run:

`python C:\temp\saas_generated_data\validate_raw_data.py`

A successful full-scale validation returns:

`{"status": "PASS", "business_rule_violations": 0, "warnings": 0}`

> **Important:** the generator recreates the `raw/` directory inside the selected output location. Use a dedicated output directory and do not point `--out` at a directory containing data that must be preserved.

## Reproducibility Verification

During repository packaging, the historical generator was re-tested to verify whether repeated runs with the same seed produced identical output.

Two reproducibility and compatibility issues were identified and corrected in the repository-maintained version.

### Deterministic selection from Python sets

The historical generator converted Python `set` objects directly back into NumPy arrays before seeded random selection.

Because set iteration order can vary between Python processes, repeated executions could produce different synthetic datasets even when the NumPy random generator used the same seed.

The repository-maintained version sorts those collections before passing them to the seeded generator.

### pandas 3.x timestamp resolution

The historical validator relied on direct `int64` conversion of datetime columns.

With pandas 3.x, different datetime columns can use different internal resolutions, such as seconds and microseconds. This can cause valid temporal intervals to fail numeric comparisons.

The repository-maintained validator normalizes parsed timestamps to microsecond resolution before interval validation.

## Full-Scale Verification Results

The corrected generator was executed independently twice at full scale.

Both runs produced:

- 49 datasets
- 2,900,948 total generated rows
- 0 datasets with different row counts
- 0 files with different SHA256 hashes
- 0 business-rule violations
- 0 validation warnings

Within the tested environment, repeated runs with the same code and seed therefore produced byte-identical raw datasets.

## Relationship to the Frozen Data Release

The generator in this directory is not the byte-for-byte reconstruction mechanism for the project's frozen input release.

The project history contains three distinct data states:

- Historical base generator output: 2,901,196 rows
- Repository-maintained deterministic generator output: 2,900,948 rows
- Frozen Data Release v1.0: 2,903,577 rows

For exact reproduction of the canonical project input, use the Frozen Data Release v1.0 rather than regenerating the data.

The frozen release remains the source of truth for the exact 49-dataset input package used by the canonical ingestion pipeline.

See:

- [`../data/README.md`](../data/README.md)
- [`../data/contracts/final_correction_override_register.csv`](../data/contracts/final_correction_override_register.csv)

## Why the Generator Is Included

The generator documents the upstream engineering used to create the synthetic source landscape, including realistic source-system modeling, temporal lifecycle generation, event-stream generation, cross-source relationships, controlled raw-data imperfections, seeded synthetic generation, and business-rule validation.

It is therefore part of the project's engineering story, while the frozen release remains the source of truth for exact end-to-end reproduction.
