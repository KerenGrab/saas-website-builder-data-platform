
# Machine Learning Extension — SaaS Website Builder

## Overview

This directory contains an exploratory Machine Learning
proof of concept for the SaaS Website Builder Data Platform.

The initial experiment predicts whether an account will
be in a Paid subscription state six calendar months
after its first transition to Paid.

The model is evaluated retrospectively using historical
features reconstructed from the existing data platform.

The underlying dataset is synthetic.

## Business Question

At the moment an account first becomes Paid, can its
previous product activity and account history help rank
its risk of being Not Paid six months later?

Target definition:

- `1`: Paid at M6
- `0`: Not Paid at M6 (Free or Closed)

Prediction timestamp: `first_paid_at`.

Observation cutoff: 2026-01-01 00:00:00 UTC.

## Directory Structure

```text
ml/
├── data/
│   └── m6_training_dataset.csv
├── discovery/
│   ├── discovery_notes.md
│   └── sql/
│       └── 01–08: discovery, validation and export SQL
├── experiments/
│   ├── m6_baseline.py
│   ├── m6_logistic_regression.py
│   ├── m6_final_evaluation.py
│   └── m6_experiment_report.md
└── README.md
```

## Dataset

The exported dataset contains 316 eligible accounts,
one row per account.

| Split | Accounts | Paid | Not Paid |
|---|---:|---:|---:|
| Train | 122 | 111 | 11 |
| Validation | 90 | 82 | 8 |
| Test | 104 | 82 | 22 |

The CSV contains 14 columns, including nine candidate
features, experiment metadata and the M6 target.

The frozen final model uses three features:

- `days_until_first_paid`
- `product_access_count`
- `locked_attempt_count`

Account IDs, timestamps and split metadata are not
used as model inputs.

The included CSV is a fixed, synthetic experiment
snapshot. Running the Python experiment does not
require a live PostgreSQL connection.

## Setup

Use Python 3.11.

From the repository root, create and activate a virtual
environment on Windows:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-ml.txt
```

The ML requirements include the base project
dependencies, pandas and scikit-learn.

## Reproduce the Experiment

Run the baseline:

```powershell
python .\ml\experiments\m6_baseline.py
```

Run the frozen holdout evaluation:

```powershell
python .\ml\experiments\m6_final_evaluation.py
```

For the exploratory model comparisons and diagnostics:

```powershell
python .\ml\experiments\m6_logistic_regression.py
```

The exploratory script uses Train and Validation.
The final evaluation script fits the frozen model on
Train + Validation and evaluates it on Test.

Running the final evaluation again reproduces the
recorded result; it is not a new independent test.

## Frozen Holdout Results

The final model is an unweighted Logistic Regression
inside a Pipeline with StandardScaler.

It was fitted on 212 accounts and evaluated on
104 Test accounts.

| Metric | Result |
|---|---:|
| Average Precision | 0.4768 |
| Not Paid prevalence reference | 0.2115 |
| Precision@10 | 70.00% |
| Recall@10 | 31.82% |
| Actual Not Paid in top 10 | 7 |

The model ranked seven actual Not Paid accounts
among the ten highest-risk accounts in the Test cohort.

No classification threshold was selected.

## Interpretation and Limitations

This is an exploratory proof of concept, not a
production-ready prediction system.

Important limitations:

- The dataset is synthetic.
- Only 19 Not Paid examples were available for the
  final model-fitting population.
- The evaluation is retrospective and does not
  simulate historical model deployment.
- The Test cohort contains 22 Not Paid examples.
- The model scores are not calibrated business
  probabilities.
- Ranking performance does not establish that
  customer interventions would prevent churn.
- Generalization to other cohorts or real customers
  has not been established.

The frozen Test results must not be used for further
model tuning while treating the same Test set as
an independent evaluation.

## Data Lineage and Documentation

The SQL files under `ml/discovery/sql/` document
how the historical features and M6 target were
reconstructed from the existing PostgreSQL schema.

See `ml/discovery/discovery_notes.md` for data
discovery, temporal contracts and validation results.

See `ml/experiments/m6_experiment_report.md` for
the exploratory experiments, frozen protocol,
holdout metrics and interpretation limits.

The ML extension does not modify the operational
database or the existing data pipeline.