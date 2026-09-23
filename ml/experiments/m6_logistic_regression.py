
from pathlib import Path

import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
)


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
    "product_access_count",
    "locked_attempt_count",
    "feature_used_count",
    "analytics_view_count",
    "other_event_count",
    "websites_created_before_paid",
    "live_websites_at_first_paid",
]

TARGET_COLUMN = "target_m6"


# ============================================================
# 3. Load dataset and validate the experiment inputs
# ============================================================

df = pd.read_csv(DATA_PATH)

assert len(df) == 316, "Unexpected dataset row count"
assert df["account_id"].is_unique, "Duplicate accounts"

assert df["split_name"].value_counts().to_dict() == {
    "TRAIN": 122,
    "VALIDATION": 90,
    "TEST": 104,
}, "Unexpected split sizes"

assert not df[
    FEATURE_COLUMNS + [TARGET_COLUMN]
].isna().any().any(), "Missing features or target"

train = df.loc[df["split_name"] == "TRAIN"].copy()

validation = df.loc[
    df["split_name"] == "VALIDATION"
].copy()


# ============================================================
# 4. Prepare X and y
#
# 0 = Not Paid
# 1 = Paid
#
# TEST remains untouched.
# ============================================================

X_train = train[FEATURE_COLUMNS]
y_train = train[TARGET_COLUMN].astype(int)

X_val = validation[FEATURE_COLUMNS]
y_val = validation[TARGET_COLUMN].astype(int)

assert set(y_train.unique()) == {0, 1}
assert set(y_val.unique()) == {0, 1}

print("======== DATASET ========")
print("Train X:", X_train.shape)
print("Train y:", y_train.shape)
print("Validation X:", X_val.shape)
print("Validation y:", y_val.shape)
print("Feature count:", len(FEATURE_COLUMNS))


# ============================================================
# 5. Build the model
#
# Pipeline prevents the scaler from learning
# statistics from Validation or Test.
#
# class_weight="balanced" gives more weight
# to the less frequent class during training.
# ============================================================

model = Pipeline(
    steps=[
        ("scaler", StandardScaler()),
        (
            "classifier",
            LogisticRegression(
                class_weight="balanced",
                max_iter=2000,
                solver="lbfgs",
            ),
        ),
    ]
)


# ============================================================
# 6. Train on TRAIN only
# ============================================================

model.fit(X_train, y_train)

print("\n======== MODEL TRAINED ========")
print("Algorithm: Logistic Regression")
print("Class weight: balanced")
print("Training completed.")


# ============================================================
# 7. Evaluation
# ============================================================

def evaluate(
    split_name: str,
    y_true: pd.Series,
    y_pred,
) -> None:

    # Rows: actual labels 0, 1
    # Columns: predicted labels 0, 1
    cm = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )

    accuracy = accuracy_score(y_true, y_pred)

    balanced_accuracy = balanced_accuracy_score(
        y_true,
        y_pred,
    )

    # Evaluate Not Paid (0) as the class of interest.
    not_paid_precision = precision_score(
        y_true,
        y_pred,
        pos_label=0,
        zero_division=0,
    )

    not_paid_recall = recall_score(
        y_true,
        y_pred,
        pos_label=0,
        zero_division=0,
    )

    not_paid_f1 = f1_score(
        y_true,
        y_pred,
        pos_label=0,
        zero_division=0,
    )

    print(f"\n======== {split_name} RESULTS ========")

    print("Accounts:", len(y_true))
    print("Actual Not Paid:", int((y_true == 0).sum()))
    print("Actual Paid:", int((y_true == 1).sum()))

    print("Predicted Not Paid:", int((y_pred == 0).sum()))
    print("Predicted Paid:", int((y_pred == 1).sum()))

    print(f"Accuracy: {accuracy:.2%}")
    print(f"Balanced accuracy: {balanced_accuracy:.2%}")

    print(f"Not Paid precision: {not_paid_precision:.2%}")
    print(f"Not Paid recall: {not_paid_recall:.2%}")
    print(f"Not Paid F1: {not_paid_f1:.2%}")

    print("\nConfusion matrix (actual rows / predicted columns)")
    print("                    Pred Not Paid    Pred Paid")
    print(f"Actual Not Paid:    {cm[0, 0]:>8} {cm[0, 1]:>13}")
    print(f"Actual Paid:        {cm[1, 0]:>8} {cm[1, 1]:>13}")


# ============================================================
# 8. Predict and evaluate TRAIN
# ============================================================

train_predictions = model.predict(X_train)

evaluate(
    "TRAIN",
    y_train,
    train_predictions,
)


# ============================================================
# 9. Predict and evaluate VALIDATION
# ============================================================

validation_predictions = model.predict(X_val)

evaluate(
    "VALIDATION",
    y_val,
    validation_predictions,
)


# ============================================================
# 10. Baseline reference
# ============================================================

print("\n======== VALIDATION BASELINE ========")
print("Always Paid accuracy: 91.11%")
print("Always Paid balanced accuracy: 50.00%")
print("Always Paid Not Paid recall: 0.00%")

print("\nTEST has not been used.")
print("Do not select a final model based on TRAIN metrics.")












# ============================================================
# 11. Controlled experiment: without class balancing
# ============================================================

unweighted_model = Pipeline(
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

# Train on the same TRAIN data
unweighted_model.fit(X_train, y_train)

# Evaluate on the same VALIDATION data
unweighted_val_predictions = unweighted_model.predict(X_val)

evaluate(
    "VALIDATION — UNWEIGHTED MODEL",
    y_val,
    unweighted_val_predictions,
)

print("\nBoth models used the same TRAIN and VALIDATION splits.")
print("TEST remains untouched.")










# ============================================================
# 12. Validation threshold analysis
#
# Explore predictions for Not Paid (class 0).
# Do not use TEST.
# ============================================================

from sklearn.metrics import average_precision_score

THRESHOLDS = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]

actual_not_paid = (y_val == 0).astype(int)


def analyze_thresholds(model_name, fitted_model):
    class_labels = list(fitted_model.classes_)

    # Find the probability column for Not Paid (0).
    not_paid_index = class_labels.index(0)

    not_paid_scores = fitted_model.predict_proba(X_val)[
        :, not_paid_index
    ]

    ap = average_precision_score(
        actual_not_paid,
        not_paid_scores,
    )

    print(f"\n======== {model_name}: THRESHOLDS ========")
    print(f"Average Precision: {ap:.4f}")
    print(f"Not Paid prevalence: {actual_not_paid.mean():.2%}")

    print(
        "Threshold | Flagged | Correct | False alarms "
        "| Missed | Precision | Recall"
    )

    for threshold in THRESHOLDS:
        predicted_not_paid = (
            not_paid_scores >= threshold
        ).astype(int)

        correct = int(
            ((predicted_not_paid == 1) & (actual_not_paid == 1)).sum()
        )

        false_alarms = int(
            ((predicted_not_paid == 1) & (actual_not_paid == 0)).sum()
        )

        missed = int(
            ((predicted_not_paid == 0) & (actual_not_paid == 1)).sum()
        )

        flagged = int(predicted_not_paid.sum())

        precision = precision_score(
            actual_not_paid,
            predicted_not_paid,
            zero_division=0,
        )

        recall = recall_score(
            actual_not_paid,
            predicted_not_paid,
            zero_division=0,
        )

        print(
            f"{threshold:>9.1f} | "
            f"{flagged:>7} | "
            f"{correct:>7} | "
            f"{false_alarms:>12} | "
            f"{missed:>6} | "
            f"{precision:>9.2%} | "
            f"{recall:>6.2%}"
        )


analyze_thresholds(
    "BALANCED MODEL",
    model,
)

analyze_thresholds(
    "UNWEIGHTED MODEL",
    unweighted_model,
)

print("\nThreshold analysis used VALIDATION only.")
print("No final threshold selected. TEST remains untouched.")








# ============================================================
# 13. Feature diagnostics
#
# Compare feature distributions by target class.
# TRAIN and VALIDATION only.
# ============================================================

def show_feature_diagnostics(split_name, subset):

    print(f"\n======== {split_name}: FEATURE DIAGNOSTICS ========")

    print("Accounts:", len(subset))
    print("Not Paid:", int((subset[TARGET_COLUMN] == 0).sum()))
    print("Paid:", int((subset[TARGET_COLUMN] == 1).sum()))

    feature_medians = (
        subset
        .groupby(TARGET_COLUMN)[FEATURE_COLUMNS]
        .median()
        .T
    )

    feature_medians = feature_medians.rename(
        columns={
            0: "Not Paid median",
            1: "Paid median",
        }
    )

    print("\nFeature medians by actual M6 target:")
    print(feature_medians.round(2).to_string())


show_feature_diagnostics("TRAIN", train)

show_feature_diagnostics("VALIDATION", validation)

print("\nFeature diagnostics completed.")
print("TEST remains untouched.")








# ============================================================
# 14. Consolidated feature review
# TRAIN and VALIDATION only.
# ============================================================

SPARSE_FEATURES = [
    "feature_used_count",
    "analytics_view_count",
    "other_event_count",
    "websites_created_before_paid",
    "live_websites_at_first_paid",
]


def show_nonzero_coverage(split_name, subset):
    print(f"\n======== {split_name}: NONZERO COVERAGE ========")

    for target, label in [(0, "Not Paid"), (1, "Paid")]:
        group = subset.loc[subset[TARGET_COLUMN] == target]

        print(f"\n{label} | accounts: {len(group)}")

        for feature in SPARSE_FEATURES:
            count = int((group[feature] > 0).sum())
            percentage = 100 * count / len(group)

            print(
                f"{feature}: "
                f"{count}/{len(group)} ({percentage:.1f}%)"
            )


show_nonzero_coverage("TRAIN", train)
show_nonzero_coverage("VALIDATION", validation)


# ============================================================
# Standardized coefficients of the balanced model
# Positive coefficient: higher model score for Paid (1).
# Negative coefficient: lower model score for Paid (1).
# These are conditional associations, not causal effects.
# ============================================================

print("\n======== BALANCED MODEL: COEFFICIENTS ========")

coefficients = pd.Series(
    model.named_steps["classifier"].coef_[0],
    index=FEATURE_COLUMNS,
)

coefficients = coefficients.sort_values(
    key=abs,
    ascending=False,
)

print(coefficients.round(4).to_string())

print("\nFeature review completed.")
print("TEST remains untouched.")




# ============================================================
# 15. Compact feature experiment
#
# Compare a smaller feature set with the existing models.
# Exploratory evaluation on VALIDATION only.
# TEST remains untouched.
# ============================================================

COMPACT_FEATURES = [
    "days_until_first_paid",
    "product_access_count",
    "locked_attempt_count",
]

X_train_compact = train[COMPACT_FEATURES]
X_val_compact = validation[COMPACT_FEATURES]

actual_not_paid = (y_val == 0).astype(int)


def run_compact_experiment(name, class_weight):

    compact_model = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "classifier",
                LogisticRegression(
                    class_weight=class_weight,
                    max_iter=2000,
                    solver="lbfgs",
                ),
            ),
        ]
    )

    compact_model.fit(
        X_train_compact,
        y_train,
    )

    predictions = compact_model.predict(
        X_val_compact
    )

    evaluate(
        name,
        y_val,
        predictions,
    )

    not_paid_index = list(
        compact_model.classes_
    ).index(0)

    not_paid_scores = compact_model.predict_proba(
        X_val_compact
    )[:, not_paid_index]

    ap = average_precision_score(
        actual_not_paid,
        not_paid_scores,
    )

    print(f"Not Paid Average Precision: {ap:.4f}")


print("\n======== COMPACT FEATURE EXPERIMENT ========")
print("Features:", COMPACT_FEATURES)

run_compact_experiment(
    "COMPACT BALANCED",
    class_weight="balanced",
)

run_compact_experiment(
    "COMPACT UNWEIGHTED",
    class_weight=None,
)

print("\nCompact experiment completed.")
print("Results are exploratory, not final model selection.")
print("TEST remains untouched.")