# End-to-End Reproduction Evidence

This document records the verified clean reproduction of the SaaS Website Builder Data Platform from the frozen input contract through PostgreSQL loading, reconciliation, data quality validation, and regression testing.

The purpose of this evidence is to demonstrate that the platform can recreate the expected business-data state from a clean database using the canonical pipeline and frozen input package.

---

## 1. Reproduction Goal

The reproduction test verified the following path:

```text
Frozen Input Package
        ↓
Input Contract Validation
        ↓
Structural Validation
        ↓
Integrity Verification
        ↓
Relationship Validation
        ↓
Streaming Ingestion
        ↓
Transformation
        ↓
Duplicate Handling
        ↓
Dependency-Aware Loading
        ↓
Atomic PostgreSQL Transaction
        ↓
Post-Load Reconciliation
        ↓
Data Quality Validation
        ↓
Regression Testing
        ↓
Verified Reproduced State
```

The reproduction was executed against a separate clean PostgreSQL database rather than an already-loaded environment.

This ensured that successful results did not depend on previously persisted business data.

---

## 2. Frozen Input Contract

The canonical frozen input package contained:

| Metric | Verified Result |
|---|---:|
| Datasets | 49 |
| CSV datasets | 44 |
| JSONL datasets | 5 |
| Raw records | 2,903,577 |
| Row-count checks | 49 / 49 PASS |
| SHA256 integrity checks | 49 / 49 PASS |

The frozen contract version used for the final reproduction was:

```text
Contract Version: 1.0
Status: FROZEN
```

---

## 3. Clean Database Starting Point

Before the full load, the target environment was verified to contain:

```text
49 / 49 required business tables
0 pre-existing business rows
Operational metadata ready
Frozen source package available
```

This established a clean and controlled reproduction starting point.

---

## 4. Pipeline Execution Sequence

The canonical verification sequence was:

```text
validate
    ↓
target-check
    ↓
full-load
    ↓
dq
    ↓
pytest
```

The pipeline validated the source package before any business-data write occurred.

The load then proceeded using the verified dependency order and the canonical transformation rules.

---

## 5. Load and Reconciliation Results

The clean full-load produced:

| Metric | Result |
|---|---:|
| Raw records processed | 2,903,577 |
| Exact duplicate deliveries skipped | 3,638 |
| Rows loaded to PostgreSQL | 2,899,939 |
| Target tables reconciled | 49 / 49 |
| Post-load reconciliation | PASS |
| Transaction outcome | COMMIT |

The row-count arithmetic is consistent:

```text
2,903,577 raw records
-   3,638 exact duplicate deliveries
-------------------------------------
2,899,939 loaded rows
```

---

## 6. Duplicate Handling Contract

Duplicate-aware event streams follow an explicit contract.

```text
First event_id
→ KEEP

Same event_id + identical payload
→ SKIP

Same event_id + different payload
→ FAIL
```

This distinguishes source-level duplicate delivery handling from full-pipeline rerun semantics.

An identical repeated event is treated as a safe duplicate delivery.

A repeated identifier with a different payload is treated as a conflict and stops processing.

---

## 7. Atomicity

The full load was executed as an atomic PostgreSQL transaction.

The verified successful path was:

```text
Validated Input
      ↓
Transform
      ↓
Load
      ↓
Reconcile
      ↓
COMMIT
```

If a load-stage failure occurs before successful completion, the transaction contract requires rollback rather than leaving a partially loaded business state.

The final reproduction completed with:

```text
Transaction: COMMIT
```

---

## 8. Data Quality Results

After loading, the canonical data-quality framework was executed against the reproduced database.

Results:

| Metric | Result |
|---|---:|
| Target tables found | 49 / 49 |
| DQ rules executed | 32 |
| DQ rules passed | 32 |
| DQ rules failed | 0 |
| Total violations | 0 |
| Overall status | PASS |

The DQ stage is read-only.

Its control behaviour is:

```text
DQ PASS
→ exit 0

DQ FAIL
→ exit 2

Framework / SQL error
→ separate exception path
```

---

## 9. Persistent Run Evidence

Operational evidence was persisted during the reproduction process.

The pipeline records execution evidence through:

```text
pipeline.log
pipeline_meta.run_history
```

Run-history metadata includes fields such as:

```text
run_id
batch_id
mode
status
validation_status
dq_status
transaction_outcome
started_at
finished_at
duration_ms
```

The successful full-load recorded the canonical batch:

```text
batch_id: canonical-contract-v1.0
status: SUCCESS
transaction: COMMIT
datasets: 49
raw records: 2,903,577
duplicates skipped: 3,638
rows loaded: 2,899,939
```

The successful DQ execution recorded:

```text
rules: 32
pass: 32
fail: 0
violations: 0
dq_status: PASS
status: SUCCESS
```

---

## 10. Regression Test Results

After the clean end-to-end reproduction, the automated test suite was executed.

Results:

```text
Tests collected: 39
Tests passed: 39
Tests failed: 0
```

The suite covers areas including:

```text
CLI behaviour
Validation
Transformation
Duplicate handling
Integrity checks
Load planning
Target safety
Reconciliation
Transactions
Rerun behaviour
Logging
Run history
Data-quality control flow
```

The regression run confirmed that the clean reproduction did not break previously verified pipeline behaviour.

---

## 11. Deterministic Business Result

The reproduction demonstrated the following invariant:

```text
Same Frozen Input
+
Same Pipeline Code
+
Same Schema / Configuration
        ↓
Same Expected Business-Data Result
```

The verified business result was:

```text
49 datasets
2,903,577 raw records
3,638 exact duplicate deliveries skipped
2,899,939 target rows
49 / 49 reconciliation PASS
32 / 32 DQ PASS
0 DQ violations
39 / 39 regression tests PASS
```

Execution-specific metadata may vary between runs, including:

```text
run_id
timestamps
duration
```

These fields describe an individual execution attempt rather than the deterministic business-data result.

---

## 12. Verification Summary

| Verification Area | Result |
|---|---|
| Clean target environment | PASS |
| Frozen input available | PASS |
| 49 / 49 datasets verified | PASS |
| 49 / 49 row counts verified | PASS |
| 49 / 49 SHA256 checks verified | PASS |
| Structural validation | PASS |
| Relationship validation | PASS |
| Target readiness | PASS |
| Full load | PASS |
| Duplicate handling | PASS |
| 49 / 49 reconciliation | PASS |
| Atomic transaction | COMMIT |
| 32 / 32 DQ rules | PASS |
| DQ violations | 0 |
| Persistent run history | VERIFIED |
| Persistent logging | VERIFIED |
| Regression tests | 39 / 39 PASS |
| Unresolved technical blockers | 0 |

---

## Final Result

```text
Clean Reproduction        VERIFIED
Frozen Input              VERIFIED
Validation                PASS
Transformation            PASS
Duplicate Handling        PASS
Dependency-Aware Loading  PASS
Atomic Transaction        COMMIT
Reconciliation            PASS
Data Quality              PASS
Operational Evidence      VERIFIED
Regression Testing        PASS
Reproducibility           VERIFIED
```

The end-to-end pipeline successfully recreated the expected PostgreSQL business-data state from the canonical frozen input package.