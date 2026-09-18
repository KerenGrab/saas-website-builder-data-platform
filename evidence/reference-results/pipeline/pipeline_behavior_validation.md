# Pipeline Behavior Validation

This document records the automated behavior-validation evidence for the SaaS Website Builder Data Platform pipeline.

The goal of this validation layer was not to re-evaluate business-data correctness. Instead, it tested whether the pipeline behaves correctly across successful execution, validation failure, duplicate delivery, transaction failure, rerun, and idempotency scenarios.

---

## 1. Validation Scope

The pipeline behavior suite covers:

```text
Validation Failures
        ↓
Integrity Failures
        ↓
Transformation & Projection
        ↓
Duplicate Handling
        ↓
Load-Plan Safety
        ↓
Target-State Protection
        ↓
Data-Quality Control Flow
        ↓
PostgreSQL Transactions
        ↓
Rerun Semantics
        ↓
Idempotency
```

The objective was to prove both normal and failure-path behavior.

---

## 2. Testing Strategy

The suite uses both unit and PostgreSQL integration tests.

### Unit Tests

Unit tests are used when behavior can be verified deterministically without persistent database writes.

They cover areas such as:

- structural validation
- relationship validation
- frozen row-count integrity
- SHA256 integrity
- dataset-specific transformations
- projection
- nullable values
- duplicate-delivery logic
- load-plan validation
- reconciliation logic
- batch identity
- deterministic fingerprinting
- rerun decisions
- DQ exit-code behavior
- CLI control flow

### Integration Tests

Integration tests are used when real persisted PostgreSQL behavior matters.

They cover:

- target-state safety
- COMMIT
- ROLLBACK
- no-partial-write guarantees
- persisted batch state
- retry after failure
- safe rerun after success
- fingerprint conflict rejection
- database-level idempotency

---

## 3. Database Safety

Database-changing tests were isolated from the canonical project database.

```text
Canonical development database
→ protected

Dedicated test database
→ saas_website_builder_test
```

The test setup protects against accidental writes by verifying that the active database is explicitly intended for testing.

The frozen input package is also treated as read-only during tests.

Failure scenarios use isolated fixtures, temporary state, and controlled test records rather than modifying the canonical source package.

---

## 4. Validation and Integrity Behavior

The following failure paths were verified.

| Behavior | Expected Result | Validation Result |
|---|---|---|
| Missing required field | Reject input | PASS |
| Unknown parent reference | Reject input | PASS |
| Frozen row-count mismatch | Reject input | PASS |
| Frozen SHA256 mismatch | Reject input | PASS |

These tests confirm that invalid or drifted input does not silently continue into the load phase.

---

## 5. Transformation and Projection

Dataset-specific transformations were tested independently.

Verified behaviors include:

| Behavior | Expected Result | Validation Result |
|---|---|---|
| Dataset-specific projection | Remove non-target fields | PASS |
| Nullable CSV handling | Empty nullable value becomes `None` | PASS |
| Redundant source field removal | Field excluded from target projection | PASS |

This verifies that transformation behavior is explicit rather than being an accidental side effect of loading.

---

## 6. Duplicate Delivery Contract

Duplicate-aware JSONL event streams follow the contract:

```text
First event_id
→ KEEP

Same event_id + identical payload
→ SKIP

Same event_id + different payload
→ FAIL
```

The automated suite verifies all three paths.

| Scenario | Expected | Result |
|---|---|---|
| First event occurrence | KEEP | PASS |
| Exact duplicate delivery | SKIP | PASS |
| Conflicting duplicate | FAIL | PASS |

This behavior applies to duplicate records inside delivered source data.

It is separate from full-pipeline rerun handling.

---

## 7. Load-Plan Validation

The pipeline uses an explicit dependency-aware load plan.

The tests verify that:

```text
All required datasets are represented
        ↓
Dependencies are consistent
        ↓
Expected target-row logic is valid
        ↓
Loading can proceed safely
```

The canonical plan covers all 49 datasets.

This protects the pipeline from loading relational child data before required parent state exists.

---

## 8. Target-State Safety

The pipeline protects against unsafe loading into unexpected existing business state.

Verified behavior:

```text
Unexpected non-empty target
→ refuse unsafe mutation
```

The test confirms that the pipeline does not proceed with destructive or ambiguous loading when the target is not in the expected state.

Existing-state reconciliation is also checked before a safe rerun is skipped.

---

## 9. Transaction Contract

The loading process is designed around an atomic transaction boundary.

```text
Successful load
→ COMMIT

Failure after partial writes
→ ROLLBACK
```

Integration tests perform real PostgreSQL writes and deliberately force a failure after writes have begun.

The verified result is:

```text
Parent write
+
Child write
+
Forced failure
        ↓
ROLLBACK
        ↓
No partial business rows remain
```

This provides executable evidence for the contract:

```text
One Batch
→ One Atomic Load Attempt
```

---

## 10. Data-Quality Control Flow

The behavior suite tests the control contract around the canonical Data Quality framework.

```text
DQ PASS
→ exit 0

DQ FAIL
→ exit 2

Framework / SQL error
→ separate exception path
```

The CLI layer also preserves the DQ failure exit code rather than converting it into a successful execution.

This distinction makes automated pipeline execution able to differentiate:

```text
Valid Data
DQ Failure
Framework Failure
```

---

## 11. Batch Identity and Fingerprinting

Rerun correctness relies on two separate concepts.

```text
batch_id
→ logical batch identity

fingerprint
→ content identity
```

The fingerprint is deterministic and derived from the normalized dataset-level SHA256 values protected by the frozen-input integrity contract.

Therefore:

```text
Same batch_id
≠
Automatically same content
```

The pipeline can distinguish a legitimate repeated execution from a conflicting reuse of an existing logical batch identifier.

---

## 12. Rerun Contract

The canonical rerun behavior is:

### Previous Attempt Failed

```text
Same batch
+
Same fingerprint
+
Previous status = FAILED
        ↓
PROCESS
```

Retry is allowed.

### Previous Attempt Succeeded

```text
Same batch
+
Same fingerprint
+
Previous status = SUCCESS
        ↓
Verify existing target state
        ↓
SKIP
```

The work is not executed again.

### Same Batch, Changed Content

```text
Same batch_id
+
Different fingerprint
        ↓
ERROR
```

The conflict is rejected and existing target state remains unchanged.

### Processing State

```text
Same batch
+
Existing status = PROCESSING
        ↓
ERROR
```

Concurrent or ambiguous repeated processing is rejected.

---

## 13. Idempotency

Idempotency is verified against actual database state rather than only against a returned status value.

The tested sequence is:

```text
First successful execution
        ↓
Target state created

Same batch + same fingerprint rerun
        ↓
Existing state verified
        ↓
Work callback not executed
        ↓
Target row count unchanged
```

Therefore:

```text
Database state before safe rerun
==
Database state after safe rerun
```

This demonstrates state-level idempotency for the tested batch workflow.

---

## 14. Failure and Retry Behavior

A failed attempt does not permanently poison the logical batch.

Verified behavior:

```text
Attempt 1
→ processing begins
→ failure occurs
→ business writes roll back
→ batch recorded as FAILED

Attempt 2
→ same batch
→ same fingerprint
→ retry allowed
→ processing succeeds
```

This provides controlled recovery without allowing duplicate successful loads.

---

## 15. Pipeline Behavior Test Inventory

The behavior-validation checkpoint contained the following test areas:

| Test Area | Tests |
|---|---:|
| CLI behavior | 1 |
| DQ control flow | 3 |
| Duplicate handling | 3 |
| Frozen integrity | 2 |
| Load plan | 3 |
| Loading reconciliation | 2 |
| Loading safety | 1 |
| Rerun behavior | 11 |
| Transactions | 2 |
| Transformation | 2 |
| Validation | 2 |
| **Total** | **32** |

The canonical behavior-testing checkpoint therefore contained:

```text
32 tests
```

---

## 16. Behavior-Test Results

The pipeline behavior suite was executed twice consecutively.

### Run 1

```text
32 collected
32 passed
0 failed
```

### Immediate Run 2

```text
32 collected
32 passed
0 failed
```

No manual cleanup was required between the two runs.

This provides evidence for:

```text
Test Independence   PASS
Test Determinism    PASS
Test Repeatability  PASS
```

---

## 17. Final Regression Context

The 32-test result above represents the dedicated pipeline behavior-testing checkpoint.

Later project stages added further coverage for logging, run history, and final end-to-end reproduction.

The final project regression suite therefore reached:

```text
39 collected
39 passed
0 failed
```

The two results refer to different checkpoints and should not be interpreted as conflicting counts:

```text
Pipeline Behavior Checkpoint
→ 32 / 32 PASS

Final End-to-End Regression
→ 39 / 39 PASS
```

The final reproduction evidence is documented separately in:

[End-to-End Reproduction Evidence](../../release-validation/end_to_end_reproduction.md)

---

## 18. Verified Behavior Summary

| Area | Result |
|---|---|
| Structural validation failure handling | PASS |
| Relationship validation failure handling | PASS |
| Frozen row-count integrity | PASS |
| SHA256 integrity | PASS |
| Transformation | PASS |
| Projection | PASS |
| Nullable-value handling | PASS |
| First duplicate-aware event occurrence | PASS |
| Exact duplicate → SKIP | PASS |
| Conflicting duplicate → FAIL | PASS |
| Load-plan integrity | PASS |
| Target-state safety | PASS |
| Existing-state reconciliation | PASS |
| DQ PASS → exit 0 | PASS |
| DQ FAIL → exit 2 | PASS |
| Framework-error separation | PASS |
| PostgreSQL COMMIT | PASS |
| PostgreSQL ROLLBACK | PASS |
| No partial writes | PASS |
| Failed-batch retry | PASS |
| Same batch + same fingerprint | PASS |
| Same batch + different fingerprint | PASS |
| PROCESSING-state protection | PASS |
| State-level idempotency | PASS |
| Canonical database isolation | PASS |
| Test repeatability | PASS |

---

## Final Result

```text
Validation Behavior       VERIFIED
Integrity Protection      VERIFIED
Duplicate Handling        VERIFIED
Load-Plan Safety          VERIFIED
Target-State Protection   VERIFIED
Transaction Atomicity     VERIFIED
Rollback                  VERIFIED
Rerun Semantics           VERIFIED
Fingerprint Protection    VERIFIED
Idempotency               VERIFIED
Database Test Isolation   VERIFIED
Behavior Test Suite       32 / 32 PASS
Final Project Regression  39 / 39 PASS
```

The automated validation layer demonstrates that the pipeline is tested not only for successful execution, but also for failure, retry, conflict, duplicate delivery, transaction rollback, and safe rerun behavior.