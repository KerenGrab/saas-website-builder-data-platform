# SaaS Website Builder — ML Discovery Notes

**Project:** SaaS Website Builder Data Platform
**Phase:** ML Extension — Business & Data Discovery
**Source Database:** `saas_website_builder_9h`
**Status:** Discovery in progress — no model trained

---

## 1. Project Objective

Extend the existing SaaS Website Builder Data Platform with a Machine Learning component.

The business objective is to understand and predict customer Paid Retention after the first transition from a Free plan to a Paid plan.

Two prediction targets have been selected for staged development.

### Target A — Paid State Prediction

Predict whether an account will be in a Paid state (Standard or Premium) at a selected future horizon after First Paid.

* Prediction type: Binary Classification.
* Paid = 1.
* Free or Closed = 0.
* Candidate horizons: M1–M12.
* First model horizon: Not yet finalized.

### Target B — Paid Time Prediction

Predict the cumulative time an account will spend in Paid plans within a selected observation window after First Paid.

* Prediction type: Quantitative target; modeling approach TBD.
* Possible targets: `paid_days` and `paid_share`.
* Paid time includes Standard and Premium.
* Reactivation periods are included.
* Transitions between Standard and Premium must not reset or duplicate Paid time.

**Development decision:** Build a shared data-preparation foundation for both targets. Develop one initial model, evaluate it, and then extend to the second target.

---

## 2. Engineering Constraints

The ML extension must reuse the existing project infrastructure.

Current constraints:

* Do not rebuild the existing PostgreSQL database.
* Do not modify the existing operational schema.
* Do not regenerate the frozen source datasets.
* Do not rewrite the existing ingestion or transformation pipeline.
* Do not modify existing dashboard metric definitions to accommodate ML.
* Use read-only SQL for the Discovery phase.
* Store new ML code and documentation separately.

Any major change to the existing platform requires explicit review.

---

## 3. Available Data Sources

The initial Discovery uses the following existing tables:

| Table                                 | Purpose                         |
| ------------------------------------- | ------------------------------- |
| `public.account`                      | Account identity                |
| `public.plan_catalog`                 | Plan identification             |
| `public.subscription_plan_period`     | Historical subscription periods |
| `public.subscription_lifecycle_event` | Subscription transitions        |
| `public.account_lifecycle_event`      | Account creation and closure    |

Potential feature sources to investigate later include product behavior, website activity and support data.

These sources have not yet been approved as predictive features.

---

## 4. Subscription History Validation

The following checks were executed against PostgreSQL.

### Subscription Population

| Metric                              | Result |
| ----------------------------------- | -----: |
| Accounts                            |  2,000 |
| Subscription periods                |  2,786 |
| Free periods                        |  2,082 |
| Standard periods                    |    567 |
| Premium periods                     |    137 |
| Ever Paid accounts                  |    600 |
| Accounts with multiple Paid periods |    103 |

Multiple Paid periods do not necessarily indicate Reactivation. They can also represent Standard-to-Premium transitions.

### Temporal Data Quality

| Check                                | Result |
| ------------------------------------ | -----: |
| Continuous transitions               |    786 |
| Gaps between consecutive periods     |      0 |
| Overlaps between consecutive periods |      0 |
| Transitions after an open period     |      0 |
| Zero-duration periods                |      0 |
| Negative-duration periods            |      0 |
| Open periods                         |  1,920 |
| Valid closed periods                 |    866 |

### Account Closure

| Metric                                       | Result |
| -------------------------------------------- | -----: |
| Closed accounts                              |     80 |
| Closed accounts without an open period       |     80 |
| Open periods associated with closed accounts |      0 |
| Exact closure timestamp matches              |     80 |
| Closure timestamp mismatches                 |      0 |

The checks confirm consistency between account closure events and the end of the final subscription period for the 80 closed accounts.

**Status:** Subscription history validation checks passed. Final ML time-boundary conventions remain to be documented.

---

## 5. First Paid Validation

The prediction point is the first valid transition from Free to a Paid plan.

First Paid was independently derived from:

1. The earliest Paid subscription period.
2. The earliest Free-to-Paid Upgrade event.

### Results

| Metric                          | Result |
| ------------------------------- | -----: |
| Accounts from Paid periods      |    600 |
| Accounts from Upgrade events    |    600 |
| Accounts matched across sources |    600 |
| Missing Upgrade events          |      0 |
| Missing Paid periods            |      0 |
| Exact timestamp matches         |    600 |
| Timestamp mismatches            |      0 |

The initial Free-to-Paid transitions include 550 Free-to-Standard and 50 Free-to-Premium events.

**Decision:** Use `first_paid_at` as the prediction timestamp.

Only information available at or before the prediction timestamp may be used to generate features. Event ordering at the exact timestamp must be handled consistently.

---

## 6. Observation Window

The frozen dataset extends through the end of December 2025.

The provisional upper observation boundary is:

`2026-01-01 00:00:00 UTC`

This is an exclusive upper boundary.

A full future horizon is required for the initial supervised-label calculations.

An account whose target date falls outside the available observation window must not automatically be classified as Not Paid.

Monthly horizons are calculated relative to each account's First Paid timestamp, using UTC calendar arithmetic.

**Open item:** Finalize and document the canonical time-boundary and month-arithmetic contract.

---

## 7. Target A — Paid State Discovery

### Eligible Population by Horizon

| Horizon | Eligible Accounts | Not Fully Observed |
| ------- | ----------------: | -----------------: |
| M1      |               573 |                 27 |
| M2      |               522 |                 78 |
| M3      |               455 |                145 |
| M4      |               404 |                196 |
| M5      |               349 |                251 |
| M6      |               316 |                284 |
| M7      |               281 |                319 |
| M8      |               250 |                350 |
| M9      |               212 |                388 |
| M10     |               182 |                418 |
| M11     |               153 |                447 |
| M12     |               122 |                478 |

### Selected Label Distributions

| Horizon | Eligible | Paid | Not Paid |
| ------- | -------: | ---: | -------: |
| M1      |      573 |  572 |        1 |
| M3      |      455 |  449 |        6 |
| M6      |      316 |  275 |       41 |
| M12     |      122 |   97 |       25 |

Unknown accounts: 0 across all 12 horizons.

### Initial Findings

* The early horizons contain very few Not Paid examples.
* M6 contains more Not Paid examples than M1 and M3.
* M12 contains fewer eligible accounts than M6.
* The label distribution changes across First Paid cohorts.
* No first-model horizon has been finalized.

---

## 8. Temporal Feasibility

A simulated model-training date of `2025-04-01 00:00:00 UTC` was evaluated for Target A at M6.

### Available Training Labels

| Metric                        | Result |
| ----------------------------- | -----: |
| Accounts with known M6 labels |     63 |
| Paid                          |     61 |
| Not Paid                      |      2 |
| Unknown                       |      0 |

This is a significant limitation for a strict historical deployment simulation.

Although 316 accounts have observable M6 outcomes by the end of the dataset, only 63 had known M6 outcomes by the simulated training date.

**Finding:** A model trained at this historical point would have only two Not Paid examples. This is insufficient evidence for reliable discrimination of the minority class.

A final Train/Validation/Test strategy has not yet been approved.

---

## 9. Target B — Paid Time Discovery

Paid Time is calculated by intersecting each account's Paid subscription periods with its observation window.

The duration is first calculated from timestamps and then converted into days.

A Standard-to-Premium transition does not duplicate time. Subsequent Paid periods following Reactivation are included.

### M6 Results

| Metric                                   | Result |
| ---------------------------------------- | -----: |
| Eligible accounts                        |    316 |
| Minimum Paid days                        |  66.71 |
| Average Paid days                        | 176.03 |
| Maximum Paid days                        | 184.00 |
| Fully Paid accounts                      |    274 |
| Partially Paid accounts                  |     42 |
| Zero Paid accounts                       |      0 |
| Average Paid days among partial accounts | 133.43 |

#### M6 Distribution

| Share of Window in Paid | Accounts |
| ----------------------- | -------: |
| 100%                    |      274 |
| 95%–less than 100%      |        3 |
| 80%–less than 95%       |       15 |
| 50%–less than 80%       |       20 |
| Less than 50%           |        4 |

### M12 Results

| Metric                  | Result |
| ----------------------- | -----: |
| Eligible accounts       |    122 |
| Average Paid days       | 331.60 |
| Minimum Paid days       |  66.71 |
| Maximum Paid days       | 365.00 |
| Fully Paid accounts     |     95 |
| Partially Paid accounts |     27 |

#### M12 Distribution

| Share of Window in Paid | Accounts |
| ----------------------- | -------: |
| 100%                    |       95 |
| 95%–less than 100%      |        1 |
| 80%–less than 95%       |        2 |
| 50%–less than 80%       |       14 |
| Less than 50%           |       10 |

Invalid-duration accounts: 0.

### Initial Findings

Target B contains quantitative information about the duration of Paid membership.

However, both M6 and M12 exhibit a high concentration of accounts that remain Paid for the entire observation window.

Target B does not automatically resolve the temporal-data limitations found in Target A.

A baseline and model evaluation are required before determining predictive usefulness.

---

## 10. Existing Analytics — Important Distinction

The existing Part 11 Headline Paid Retention metric uses a documented population of 143 accounts for M12.

The current ML Discovery identified 122 accounts with a complete timestamp-based M12 horizon.

These populations are not assumed to be equivalent.

The existing analytics contract and the proposed ML-label contract must be compared and documented before final model development.

Do not alter historical analytics results merely to match the ML calculations.

---

## 11. Current ML Feasibility Status

| Area                                    | Status               |
| --------------------------------------- | -------------------- |
| Subscription history                    | Validated            |
| Account closure reconciliation          | Validated            |
| First Paid identification               | Validated            |
| Initial observation cutoff              | Provisional          |
| Target A label discovery                | Completed for M1–M12 |
| Target B M6/M12 distribution            | Completed            |
| Feature Discovery                       | Not started          |
| Final target and horizon selection      | Pending              |
| Temporal Train/Validation/Test strategy | Pending              |
| Baseline                                | Not trained          |
| ML model                                | Not trained          |
| ML pipeline integration                 | Not started          |

The Discovery phase is still open.

---

## 12. Next Steps

The next phase is Feature Discovery.

We will investigate which account-level features can be calculated using only information available at First Paid.

Candidate areas:

* Account age before First Paid.
* Duration of Free membership.
* Product behavior before First Paid.
* Website activity before First Paid.
* Support interactions before First Paid.

Before model training, we must also:

1. Finalize the time-boundary and target contracts.
2. Check feature availability and missing values.
3. Verify that feature timestamps do not introduce leakage.
4. Evaluate chronological training and test feasibility.
5. Define baseline predictions and evaluation metrics.
6. Decide which target and horizon to implement first.

**Final working principle:** Adapt the ML extension to the existing data platform. Do not rebuild the platform or generate additional data merely to improve modeling results.

---

## 13. Discovery Artifacts

SQL files currently created:

`ml/discovery/sql/01_paid_time_m12_distribution.sql`

Discovery documentation:

`ml/discovery/discovery_notes.md`

The M6 and M12 results were obtained using read-only SQL against the existing PostgreSQL database.

No ML model has been trained, and no changes have been made to the operational database as part of this Discovery.





---

## 14. Feature Discovery — Feature 01

### Days Until First Paid

**Feature name:** `days_until_first_paid`

**Definition:** Number of days between account creation and the first transition to a Paid subscription.

**Prediction timestamp:** `first_paid_at`

**Grain:** One row per Ever Paid account.

**Source tables:**
- `public.account_lifecycle_event`
- `public.subscription_plan_period`
- `public.plan_catalog`

### Validation Results

| Metric | Result |
|---|---:|
| Accounts | 600 |
| Missing creation dates | 0 |
| Negative durations | 0 |
| Minimum days | 14.03 |
| Average days | 63.63 |
| Maximum days | 119.29 |

**Status:** Data validation passed.

The feature can be calculated for all 600 Ever Paid accounts using information available at First Paid.

Predictive usefulness has not yet been evaluated.

**SQL artifact:** `ml/discovery/sql/02_days_until_first_paid.sql`







---

## 15. Feature Discovery — Feature 02

### Product Activity Before First Paid

**Prediction timestamp:** `first_paid_at`

**Grain:** One row per Ever Paid account.

**Source tables:**
- `public.subscription_plan_period`
- `public.plan_catalog`
- `public.account_lifecycle_event`
- `public.product_behaviour_event`

### Feature Definitions

All features are calculated using product events within:

`account_created <= event_time < first_paid_at`

| Feature | Definition |
|---|---|
| `total_product_events` | Total product events before First Paid |
| `product_access_count` | Product access events |
| `locked_attempt_count` | Locked feature attempts |
| `feature_used_count` | Feature usage events |
| `analytics_view_count` | Website analytics view events |
| `other_event_count` | Other product events |

### Validation Results

| Metric | Result |
|---|---:|
| Ever Paid accounts | 600 |
| Account-level feature rows | 600 |
| Distinct accounts | 600 |
| Accounts with prior activity | 600 |
| Accounts without prior activity | 0 |
| Total pre-paid events | 24,949 |
| Events before account creation | 0 |
| Product access events | 16,342 |
| Locked feature attempts | 6,080 |
| Feature usage events | 1,161 |
| Analytics view events | 675 |
| Other events | 691 |

### Initial Activity Distribution

| Metric | Result |
|---|---:|
| Minimum events per account | 8 |
| Average events per account | 41.58 |
| Maximum events per account | 359 |

### Discovery Findings

Pre-paid product activity is available for all 600 Ever Paid accounts.

Account-level event counts reconcile with the previously validated
source-event totals.

The feature extraction uses only historical events before First Paid.

The predictive usefulness of these features has not yet been evaluated.

The full event type represented by `other_event_count` should be
identified before final feature selection.

**Status:** Initial data validation passed. Feature selection pending.

**SQL artifact:** `ml/discovery/sql/03_product_activity_before_paid.sql`





---

## 16. Feature Discovery — Feature 03

### Websites Created Before First Paid

**Feature name:** `websites_created_before_paid`

**Definition:** Number of distinct websites created by an
account before its first transition to a Paid subscription.

**Prediction timestamp:** `first_paid_at`

**Grain:** One row per Ever Paid account.

**Source tables:**
- `public.subscription_plan_period`
- `public.plan_catalog`
- `public.website`
- `public.website_lifecycle_event`

### Temporal Contract

Website creation is identified using the `website_created`
lifecycle event.

Only websites satisfying the following condition are counted:

`website_created_at < first_paid_at`

Websites created at or after First Paid are excluded.

### Validation Results

| Metric | Result |
|---|---:|
| Ever Paid accounts | 600 |
| Total websites belonging to Ever Paid accounts | 993 |
| Websites missing creation events | 0 |
| Websites created before account creation | 0 |
| Websites created before First Paid | 402 |
| Websites created at or after First Paid | 591 |
| Accounts with prior websites | 286 |
| Accounts without prior websites | 314 |
| Minimum websites per account | 0 |
| Average websites per account | 0.67 |
| Maximum websites per account | 5 |

### Feature Distribution

| Websites Before First Paid | Accounts |
|---|---:|
| 0 | 314 |
| 1 | 204 |
| 2 | 57 |
| 3 | 17 |
| 4 | 7 |
| 5 | 1 |
| Total | 600 |

### Discovery Findings

The feature can be calculated for all 600 Ever Paid accounts.

Website creation timestamps were validated against account
creation timestamps.

The account-level distribution reconciles to 402 websites
created before First Paid.

The feature counts website creation history. It does not
represent the number of currently live or published websites.

Predictive usefulness has not yet been evaluated.

**Status:** Initial data validation passed.
Final feature selection pending.

**SQL artifact:**
`ml/discovery/sql/04_websites_created_before_paid.sql`




---

## 17. Feature Discovery — Feature 04

### Live Websites at First Paid

**Feature name:** `live_websites_at_first_paid`

**Definition:** Number of distinct websites that were Live
at the account's first transition to a Paid subscription.

**Prediction timestamp:** `first_paid_at`

**Grain:** One row per Ever Paid account.

**Source tables:**
- `public.subscription_plan_period`
- `public.plan_catalog`
- `public.website`
- `public.website_lifecycle_event`
- `public.website_live_period`

### Temporal Contract

A website is counted only when:

1. Its creation timestamp is earlier than First Paid.
2. A Live period started before First Paid.
3. The Live period had not ended at First Paid.

The feature is reconstructed using historical website
creation events and Live periods.

Each website is counted at most once per account.

### Validation Results

| Metric | Result |
|---|---:|
| Ever Paid accounts | 600 |
| Accounts with prior websites | 286 |
| Total prior websites | 402 |
| Accounts with Live websites | 156 |
| Accounts without Live websites | 444 |
| Total Live websites | 195 |
| Minimum Live websites per account | 0 |
| Average Live websites per account | 0.33 |
| Maximum Live websites per account | 3 |

### Feature Distribution

| Live Websites at First Paid | Accounts |
|---|---:|
| 0 | 444 |
| 1 | 123 |
| 2 | 27 |
| 3 | 6 |
| Total | 600 |

### Data Quality Validation

| Check | Result |
|---|---:|
| Total Live periods | 2,497 |
| Zero-duration periods | 0 |
| Negative-duration periods | 0 |
| Periods missing creation events | 0 |
| Periods starting before website creation | 0 |
| Overlapping Live periods | 0 |
| Websites with overlapping periods | 0 |

### Consolidated Reconciliation

| Check | Result |
|---|---:|
| Missing creation events | 0 |
| Accounts where Live exceeds Created | 0 |
| Distribution account difference | 0 |
| Distribution Live difference | 0 |

All consolidated reconciliation checks passed.

### Discovery Findings

The feature can be calculated for all 600 Ever Paid accounts.

156 accounts had at least one Live website at First Paid.

The feature represents historical Live state at prediction
time, not the website's current state.

Predictive usefulness has not yet been evaluated.

**Status:** Initial data validation passed.
Final feature selection pending.

**SQL artifact:**
`ml/discovery/sql/05_live_websites_at_first_paid.sql`