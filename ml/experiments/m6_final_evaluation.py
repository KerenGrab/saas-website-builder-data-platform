
from pathlib import Path

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score


# ============================================================
# M6 Paid Retention — Frozen Holdout Evaluation
#
# Protocol:
#   Model: Logistic Regression, unweighted
#   Features: Compact (3)
#   Fit: TRAIN + VALIDATION
#   Evaluate: TEST once
#   Primary metric: Not Paid Average Precision
#
# Do not change the configuration based on TEST results.
# ============================================================


# 1. Configuration

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "m6_training_dataset.csv"
)

FEATURE_COLUMNS = [
    "days_until_first_paid",
    "product_access_count",
    "locked_attempt_count",
]

TARGET_COLUMN = "target_m6"

EXPECTED_SPLITS = {
    "TRAIN": 122,
    "VALIDATION": 90,
    "TEST": 104,
}


# 2. Load and validate the existing dataset

df = pd.read_csv(DATA_PATH)

required_columns = [
    "account_id",
    "split_name",
    TARGET_COLUMN,
    *FEATURE_COLUMNS,
]

assert all(
    column in df.columns for column in required_columns
), "Missing required columns"

assert len(df) == 316, "Unexpected dataset size"

assert df["account_id"].is_unique, (
    "Duplicate account IDs"
)

assert df["split_name"].value_counts().to_dict() == (
    EXPECTED_SPLITS
), "Unexpected split sizes"

assert not df[required_columns].isna().any().any(), (
    "Missing required values"
)

assert set(df[TARGET_COLUMN].unique()) == {0, 1}, (
    "Unexpected target labels"
)

assert all(
    pd.api.types.is_numeric_dtype(df[column])
    for column in FEATURE_COLUMNS
), "Non-numeric feature detected"


# 3. Prepare the frozen training and test populations

fit_data = df.loc[
    df["split_name"].isin(["TRAIN", "VALIDATION"])
].copy()

test_data = df.loc[
    df["split_name"] == "TEST"
].copy()

X_fit = fit_data[FEATURE_COLUMNS]
y_fit = fit_data[TARGET_COLUMN].astype(int)

X_test = test_data[FEATURE_COLUMNS]
y_test = test_data[TARGET_COLUMN].astype(int)

assert len(fit_data) == 212
assert len(test_data) == 104

assert int((y_fit == 0).sum()) == 19
assert int((y_fit == 1).sum()) == 193

assert int((y_test == 0).sum()) == 22
assert int((y_test == 1).sum()) == 82

print("======== FROZEN EXPERIMENT ========")
print("Model: Logistic Regression")
print("Class weight: None")
print("Features:", FEATURE_COLUMNS)

print("\n======== POPULATION ========")
print("Fit accounts:", len(fit_data))
print("Fit Not Paid:", int((y_fit == 0).sum()))
print("Fit Paid:", int((y_fit == 1).sum()))
print("Test accounts:", len(test_data))
print("Test Not Paid:", int((y_test == 0).sum()))
print("Test Paid:", int((y_test == 1).sum()))


# 4. Construct and fit the frozen Pipeline
#
# Both the scaler and model learn from
# TRAIN + VALIDATION only.

final_model = Pipeline(
    steps=[
        ("scaler", StandardScaler()),
        (
            "classifier",
            LogisticRegression(
                class_weight=None,
                max_iter=2000,
                solver="lbfgs",
            ),
        ),
    ]
)

final_model.fit(X_fit, y_fit)

print("\n======== MODEL FIT COMPLETED ========")


# 5. Obtain Not Paid scores for TEST
#
# The model was fitted with labels:
#   0 = Not Paid
#   1 = Paid
#
# Select the probability column corresponding to 0.

not_paid_index = list(
    final_model.classes_
).index(0)

test_scores = final_model.predict_proba(
    X_test
)[:, not_paid_index]

actual_not_paid = (y_test == 0).astype(int)


# 6. Primary metric: Average Precision

test_ap = average_precision_score(
    actual_not_paid,
    test_scores,
)

test_prevalence = actual_not_paid.mean()

print("\n======== TEST: PRIMARY METRIC ========")
print(f"Average Precision: {test_ap:.4f}")
print(
    f"Not Paid prevalence reference: "
    f"{test_prevalence:.4f}"
)


# 7. Prespecified ranking analysis: Top 10

ranking = pd.DataFrame({
    "account_id": test_data["account_id"].astype(str).to_numpy(),
    "not_paid_score": test_scores,
    "actual_not_paid": actual_not_paid.to_numpy(),
})

ranking = ranking.sort_values(
    by=["not_paid_score", "account_id"],
    ascending=[False, True],
    kind="mergesort",
)

top_10 = ranking.head(10)

correct_in_top_10 = int(
    top_10["actual_not_paid"].sum()
)

total_not_paid = int(
    actual_not_paid.sum()
)

precision_at_10 = correct_in_top_10 / 10
recall_at_10 = correct_in_top_10 / total_not_paid

print("\n======== TEST: TOP-10 RANKING ========")
print("Accounts ranked:", len(ranking))
print("Top-K:", 10)
print("Actual Not Paid in Top 10:", correct_in_top_10)

print(f"Precision@10: {precision_at_10:.2%}")
print(f"Recall@10: {recall_at_10:.2%}")


# 8. Completion status

print("\n======== EVALUATION STATUS ========")
print("Frozen configuration evaluated.")
print("TEST was not used for fitting.")
print("No decision threshold was selected.")
print("Do not tune the model based on these results.")