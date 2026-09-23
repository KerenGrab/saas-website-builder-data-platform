
# M6 Paid Retention — Initial ML Experiment Report

## 1. Objective

Predict whether an account is Paid six calendar months after
its first transition to a Paid subscription.

- Prediction timestamp: first_paid_at
- Target: 1 = Paid; 0 = Not Paid
- Experiment type: retrospective chronological evaluation
- Observation cutoff: 2026-01-01 00:00:00 UTC

## 2. Dataset

316 eligible accounts.

| Split | Accounts | Paid | Not Paid |
|---|---:|---:|---:|
| Train | 122 | 111 | 11 |
| Validation | 90 | 82 | 8 |
| Test | 104 | 82 | 22 |

Test was not used in the initial experiments.

The chronological split is retrospective. It does not
simulate model training at the start of each subsequent
cohort, because some M6 labels were unavailable then.

## 3. Models

Baseline: Always Paid.

Logistic Regression configurations:
- Full Balanced: 8 features, class_weight="balanced"
- Full Unweighted: 8 features, class_weight=None
- Compact Balanced: 3 features, class_weight="balanced"
- Compact Unweighted: 3 features, class_weight=None

All Logistic Regression configurations used StandardScaler
fitted on Train only.

Compact features:
- days_until_first_paid
- product_access_count
- locked_attempt_count

## 4. Validation Results

| Configuration | Accuracy | Not Paid Recall | Not Paid Precision | AP |
|---|---:|---:|---:|---:|
| Always Paid | 91.11% | 0.00% | 0.00% | N/A |
| Full Balanced | 53.33% | 75.00% | 13.04% | 0.2672 |
| Full Unweighted | 90.00% | 12.50% | 33.33% | 0.2792 |
| Compact Balanced | 43.33% | 75.00% | 10.91% | 0.4170 |
| Compact Unweighted | 92.22% | 12.50% | 100.00% | 0.4350 |

Not Paid prevalence in Validation: 8.89%.

## 5. Findings

Compact configurations achieved higher Average Precision
than the corresponding full configurations on Validation.

However, classification performance remained sensitive
to class weighting and decision thresholds.

Compact Unweighted flagged only one account at the
default threshold of 0.5. Its 100% Not Paid precision
therefore reflects one correct prediction, not reliable
generalization.

The balanced configurations detected six of eight
Not Paid accounts but generated many false alarms.

Several full-model features were sparse, and some
class-level patterns differed between Train and Validation.

These findings are exploratory. Repeated experimentation
on the same small Validation set limits confidence in
the observed differences.

## 6. Current Limitations

- Only 11 Not Paid training examples.
- Only 8 Not Paid validation examples.
- Retrospective split, not a historical deployment simulation.
- Feature importance and coefficients are not proven stable.
- Predicted probabilities have not been calibrated.
- No business cost or intervention policy has been defined.
- No final model or operating threshold has been selected.
- Test remains untouched.

## 7. Status and Next Decision

Initial baseline, model comparison, threshold exploration
and feature diagnostics completed.

Status: Exploratory proof of concept.

Next: Review the evaluation protocol and data feasibility
before freezing a final candidate for independent testing.

Do not claim production readiness or deploy the model.





---

## 8. Experiment Freeze — Final Holdout Evaluation

### 8.1 Decision

The initial exploratory experiments are complete.

The following configuration is frozen for a single
retrospective holdout evaluation:

- Model: Logistic Regression
- Feature set: Compact (3 features)
- Class weighting: None
- Preprocessing: StandardScaler inside a Pipeline
- Solver: lbfgs
- Maximum iterations: 2000
- Primary evaluation task: Not Paid risk ranking

The configuration was selected following exploratory
Validation analysis. Selection is not evidence of
reliable superiority over alternative configurations.

### 8.2 Frozen Features

The model will use exactly these features:

1. days_until_first_paid
2. product_access_count
3. locked_attempt_count

The account identifier, timestamps, split name, target,
and other feature columns must not be used as model inputs.

### 8.3 Training and Holdout Population

| Population | Accounts | Paid | Not Paid |
|---|---:|---:|---:|
| Train + Validation | 212 | 193 | 19 |
| Test | 104 | 82 | 22 |

The frozen Pipeline will be fitted from scratch using
Train and Validation together.

Both StandardScaler and Logistic Regression will be
fitted exclusively on these 212 accounts.

The Test population will not be used for fitting,
feature selection, threshold tuning, or calibration.

### 8.4 Prediction Scores

The model's probability output for class 0 (Not Paid)
will be used as the risk-ranking score.

Higher scores indicate higher model-estimated risk
of being Not Paid at M6.

These scores are not treated as calibrated business
probabilities.

No classification threshold will be selected for
the primary holdout evaluation.

### 8.5 Prespecified Metrics

Primary metric:

- Average Precision (AP), with Not Paid as the
  positive class for evaluation.

Reference:

- Test Not Paid prevalence: 22 / 104 = 21.15%.
- This prevalence is the constant-score AP reference.

Supporting ranking metrics:

- Precision@10
- Recall@10
- Number of actual Not Paid accounts in the top 10

Accounts will be ranked by descending Not Paid score.
Account ID will be used as a deterministic secondary
sort key if scores are tied.

No additional model configuration or threshold will be
chosen after inspecting the Test results.

### 8.6 Evaluation Protocol

1. Load and validate the existing CSV.
2. Select the frozen three-feature set.
3. Combine TRAIN and VALIDATION for model fitting.
4. Fit a new Pipeline on the combined population.
5. Produce Not Paid scores for TEST.
6. Calculate the prespecified metrics.
7. Record results and limitations.
8. Do not re-tune the model using TEST.

The initial Test evaluation will be run once under
this frozen protocol.

### 8.7 Interpretation Limits

This is a retrospective chronological evaluation,
not a historical deployment simulation.

The Test label distribution is already known from
SQL discovery, but Test model performance has not
been inspected or used for model selection.

The combined fitting population contains only
19 Not Paid examples. Test contains 22 Not Paid
examples. Estimates remain sensitive to sample size.

Multiple prior experiments were conducted on the
same small Validation set, creating model-selection
uncertainty.

The holdout result will describe performance on
this dataset and cohort. It will not establish
production readiness, causal relationships, or
stable performance on future customers.

### 8.8 Freeze Status

Status: PROTOCOL FROZEN — TEST NOT YET RUN.

The next step is to implement and execute the
prespecified holdout evaluation.






---

## 9. Final Holdout Evaluation Results

### 9.1 Execution

The frozen holdout evaluation was executed successfully.

Script: `ml/experiments/m6_final_evaluation.py`

Model configuration:
- Logistic Regression
- Compact feature set (3 features)
- `class_weight=None`
- `StandardScaler` inside a Pipeline
- `solver="lbfgs"`
- `max_iter=2000`

The model and scaler were fitted from scratch using
TRAIN and VALIDATION only.

No decision threshold was selected.

### 9.2 Evaluation Population

| Population | Accounts | Paid | Not Paid |
|---|---:|---:|---:|
| Train + Validation | 212 | 193 | 19 |
| Test | 104 | 82 | 22 |

### 9.3 Prespecified Test Metrics

| Metric | Result |
|---|---:|
| Average Precision | 0.4768 |
| Not Paid prevalence reference | 0.2115 |
| Accounts in Top-K | 10 |
| Actual Not Paid in Top 10 | 7 |
| Precision@10 | 70.00% |
| Recall@10 | 31.82% |

The model ranked seven actual Not Paid accounts
among the ten highest-risk accounts.

The remaining 15 Not Paid accounts were outside
the top ten.

### 9.4 Interpretation

The holdout results indicate positive risk-ranking
signal within the evaluated retrospective Test cohort.

Average Precision exceeded the constant-score
prevalence reference.

The results do not establish calibrated probabilities,
a suitable intervention threshold, causal effects,
production readiness, or stable future performance.

The Test label prevalence differed from Validation,
and the model was refitted on Train + Validation
before Test evaluation. The AP values from these
evaluations are therefore not a direct measure
of model improvement.

### 9.5 Evaluation Integrity

The frozen configuration was used without modification.

TEST was not used for model fitting, feature selection,
threshold tuning, or calibration.

No model changes will be made based on this Test result
and presented as part of the same independent evaluation.

### 9.6 Final Status

Initial M6 Paid Retention ML proof of concept:
COMPLETED AND EVALUATED.

The result is suitable for documented exploratory
portfolio work, with explicit limitations.

Further development requires a separately planned
iteration and evaluation protocol.

The model is not production-ready.