

from pathlib import Path

import pandas as pd


# ============================================================
# 1. Dataset location
# ============================================================

DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "m6_training_dataset.csv"
)


# ============================================================
# 2. Feature and target definitions
# ============================================================

FEATURE_COLUMNS = [
    "days_until_first_paid",
    "total_product_events",
    "product_access_count",
    "locked_attempt_count",
    "feature_used_count",
    "analytics_view_count",
    "other_event_count",
    "websites_created_before_paid",
    "live_websites_at_first_paid",
]

TARGET_COLUMN = "target_m6"

EXPECTED_SPLITS = {
    "TRAIN": 122,
    "VALIDATION": 90,
    "TEST": 104,
}


# ============================================================
# 3. Load and validate the CSV
# ============================================================

df = pd.read_csv(DATA_PATH)

assert len(df) == 316, "Unexpected dataset row count"

assert df["account_id"].is_unique, (
    "Duplicate account IDs detected"
)

assert not df[FEATURE_COLUMNS + [TARGET_COLUMN]].isna().any().any(), (
    "Missing feature or target values detected"
)

assert set(df[TARGET_COLUMN].unique()) == {0, 1}, (
    "Unexpected target values"
)

assert df["split_name"].value_counts().to_dict() == EXPECTED_SPLITS, (
    "Unexpected split sizes"
)

print("======== DATASET LOADED ========")
print("Dataset shape:", df.shape)
print("Unique accounts:", df["account_id"].nunique())


# ============================================================
# 4. Separate features (X) and target (y)
# ============================================================

X = df[FEATURE_COLUMNS].copy()

y = df[TARGET_COLUMN].astype(int).copy()

print("\n======== X / y ========")
print("X shape:", X.shape)
print("y shape:", y.shape)
print("Feature count:", X.shape[1])


# ============================================================
# 5. Evaluate Always Paid baseline
# ============================================================

def evaluate_always_paid(split_name: str) -> None:
    mask = df["split_name"] == split_name

    y_true = y.loc[mask]

    # Baseline: predict Paid (1) for every account.
    y_pred = pd.Series(1, index=y_true.index)

    accuracy = (y_pred == y_true).mean()

    paid_mask = y_true == 1
    not_paid_mask = y_true == 0

    paid_recall = (y_pred[paid_mask] == 1).mean()
    not_paid_recall = (y_pred[not_paid_mask] == 0).mean()

    balanced_accuracy = (
        paid_recall + not_paid_recall
    ) / 2

    print(f"\n======== {split_name} BASELINE ========")
    print("Accounts:", len(y_true))
    print("Actual Paid:", int(paid_mask.sum()))
    print("Actual Not Paid:", int(not_paid_mask.sum()))

    print(f"Accuracy: {accuracy:.2%}")
    print(f"Paid recall: {paid_recall:.2%}")
    print(f"Not Paid recall: {not_paid_recall:.2%}")
    print(f"Balanced accuracy: {balanced_accuracy:.2%}")


# ============================================================
# 6. Train and Validation baseline
# ============================================================

evaluate_always_paid("TRAIN")
evaluate_always_paid("VALIDATION")

print("\nTEST is reserved for final model evaluation.")
print("No machine learning model has been trained yet.")