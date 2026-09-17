# Reliability & Validation

This section explains how reliability was designed across the data platform.

A successful pipeline run does not automatically mean that the data is correct.

A system may complete without raising an exception while still containing:

- invalid input
- broken relationships
- duplicated business records
- partial loads
- incorrect historical states
- inconsistent analytical outputs
- dashboard values that do not match their intended metric definitions

For that reason, reliability in this project is implemented as multiple validation layers.

```text
Source Data
     ↓
Input Contracts
     ↓
Pre-Load Validation
     ↓
Transformation & Integrity Checks
     ↓
Transactional Load
     ↓
Database Constraints
     ↓
Post-Load Data Quality
     ↓
Reconciliation
     ↓
Analytical / Serving Validation
     ↓
Power BI
```

Software tests and run history operate across these layers.

The goal is not simply to make the pipeline run.

The goal is to make failures visible, explainable and recoverable.

---

## 1. Reliability as Defense in Depth

No single validation mechanism can protect the entire system.

Different failures occur at different stages.

For example:

```text
Wrong file structure
        ↓
Input Validation

Broken parent-child relationship
        ↓
Integrity Validation

Failure during multi-table load
        ↓
Transaction / Rollback

Unexpected business state
        ↓
Data Quality

Incorrect serving aggregation
        ↓
Serving Validation
```

Each layer therefore has a different responsibility.

This is why the project keeps concepts such as:

```text
Validation
≠
Software Testing
≠
Data Quality
≠
Reconciliation
≠
Serving Validation
```

separate rather than combining everything into a single generic test category.

---

## 2. Input Contracts

Reliability begins before a file is loaded.

Each source dataset is expected to follow a defined contract.

A source contract may describe:

- expected file
- file format
- required fields
- identifiers
- expected structure
- relationship expectations
- integrity expectations
- reference row counts
- fingerprints or checksums

The purpose of the contract is to establish:

> What input is the pipeline expecting?

Without an explicit expectation, the system cannot reliably determine whether a changed source is valid or accidental.

---

## 3. Validation Before Load

One of the main platform principles is:

> Validate before modifying the database.

Pre-load validation checks whether the incoming data is acceptable before business tables are changed.

Validation may include:

- structural checks
- required-column checks
- value validation
- type validation
- identifier validation
- missing-value rules
- allowed-value checks
- relationship checks
- cross-file integrity checks

Conceptually:

```text
Source Files
     ↓
Validation
     ↓
Valid?
 ┌───┴───┐
Yes      No
 ↓        ↓
Continue STOP
```

This reduces the risk that known-invalid source data enters the database.

---

## 4. Structural Validation vs Business Validation

Not every validation rule asks the same type of question.

A structural check may ask:

> Does this column exist?

A value check may ask:

> Is this value allowed?

A relationship check may ask:

> Does this child identifier reference an existing parent?

A business check may ask:

> Can this state logically exist according to the domain model?

Separating these concepts improves debugging because a failure can be associated with the layer that owns the problem.

---

## 5. Integrity Across Datasets

The source package contains related datasets.

A file can therefore be valid by itself while still being inconsistent with another file.

For example:

```text
Child Record
     ↓
References Parent ID
     ↓
Parent Exists?
```

Cross-source integrity checks are used to detect these problems before loading.

This is especially important in a relational model with many foreign-key relationships.

---

## 6. Database Constraints

Pipeline validation is not the only protection layer.

PostgreSQL also enforces structural integrity.

The database implementation uses mechanisms such as:

- PRIMARY KEY
- FOREIGN KEY
- UNIQUE
- CHECK constraints
- historical consistency rules

This creates two complementary protections:

```text
Pipeline Validation
        ↓
Detect problems before load

Database Constraints
        ↓
Reject invalid persisted state
```

The pipeline should not rely solely on the database to discover problems.

The database should not rely solely on Python to preserve integrity.

---

## 7. Transactional Safety

A multi-table batch can fail after some operations have already succeeded.

Without transactional protection, this can leave the database in a partially updated state.

The platform therefore uses an atomic loading strategy.

```text
BEGIN
  ↓
Load Table A
  ↓
Load Table B
  ↓
Load Table C
  ↓
Everything Successful?
   ├── Yes → COMMIT
   └── No  → ROLLBACK
```

The intended guarantee is:

> A failed business load should not leave a partially loaded business state behind.

This behavior is especially important when child tables depend on previously loaded parent tables.

---

## 8. Failure Is Part of the Design

Reliability is not only about the successful path.

The project also defines expected behavior when something goes wrong.

Examples include:

```text
Invalid Input
      ↓
STOP before load

Conflicting Duplicate
      ↓
STOP

Load Failure
      ↓
ROLLBACK

Known Identical Rerun
      ↓
SKIP

Unexpected Batch Change
      ↓
STOP
```

A system is easier to trust when failure behavior is explicit rather than accidental.

---

## 9. Duplicate Delivery Handling

Event-oriented sources may deliver the same event more than once.

The project distinguishes between two cases.

### Identical Duplicate

```text
same event_id
+
same payload
=
same business event delivered again
```

This is treated as a duplicate delivery.

It can be skipped safely according to the documented deduplication policy.

### Conflicting Duplicate

```text
same event_id
+
different payload
=
conflict
```

This is treated as a data-integrity problem.

The system should not silently select one version.

This distinction avoids confusing operational redelivery with contradictory business data.

---

## 10. Rerun Safety

Pipelines often need to be rerun.

A rerun may happen because of:

- retry after failure
- debugging
- verification
- repeated execution
- operational recovery

The documented rerun semantics include:

```text
same batch_id
+
same fingerprint
        ↓
SKIP
```

and:

```text
same batch_id
+
different fingerprint
        ↓
STOP
```

This helps protect against accidentally processing changed data under the identity of a previously known batch.

---

## 11. Batch Identity and Run Identity

The project distinguishes between:

### Batch Identity

The logical source unit being processed.

### Run Identity

A specific attempt to process it.

Conceptually:

```text
Batch A
  │
  ├── Run 1
  ├── Run 2
  └── Run 3
```

This allows execution history to distinguish:

- what data was being processed
- how many attempts occurred
- whether an attempt failed
- whether a rerun was skipped
- which run produced a result

This distinction improves traceability.

---

## 12. Software Tests

Software tests validate implementation behavior.

They are not the same thing as Data Quality checks.

Tests can verify behavior such as:

- expected successful execution
- validation failures
- duplicate handling
- rerun behavior
- rollback behavior
- database interaction
- run-history behavior
- command-line behavior

The documented reference implementation includes **39 software tests**.

This count should be interpreted as a software-test suite, not as a total count of every validation mechanism in the project.

The final public test suite will be linked here after canonical pipeline selection.

---

## 13. Data Quality

Data Quality operates after the data has been loaded.

Its question is different from pre-load validation.

```text
Validation:
Can this input enter the system?

Data Quality:
Does the resulting database state make sense?
```

Data Quality checks can detect issues such as:

- broken business relationships
- inconsistent states
- impossible combinations
- incorrect historical conditions
- unexpected counts
- population inconsistencies

The documented reference version includes **32 Data Quality rules**.

These rules are separate from the software-test suite.

---

## 14. Why Data Quality Is Separate

Consider a source file that is structurally perfect.

It may contain:

- every required column
- valid data types
- valid identifiers

but still create a logically incorrect database state.

For example:

```text
Technically Valid Record
        ↓
Loads Successfully
        ↓
Creates Impossible Business State
```

Pre-load schema validation alone may not detect this.

Post-load Data Quality therefore acts as a second type of protection.

---

## 15. Reconciliation

A successful database write does not prove that the expected amount of data arrived.

Reconciliation compares source expectations with the loaded result.

The basic reasoning is:

```text
Raw Source Count
      ↓
Expected Transformations
      ↓
Expected Deduplication
      ↓
Expected Target Count
      ↓
Actual Target Count
      ↓
Match?
```

This allows differences to be explained instead of treated automatically as data loss.

---

## 16. Duplicate-Aware Reconciliation

The frozen source package contains documented identical duplicate deliveries.

This means:

```text
Raw Records
      ↓
Remove Known Identical Duplicate Deliveries
      ↓
Expected Target Records
```

A lower target count can therefore be correct.

The important requirement is that the difference must be explainable through documented rules.

The current reference package records:

```text
2,903,577 raw records
        ↓
3,638 identical duplicate deliveries
        ↓
2,899,939 expected target rows
```

These figures will be linked to their reference evidence in the public evidence layer.

---

## 17. Serving Validation

Even if the operational database is correct, the dashboard can still receive incorrect analytical outputs.

The serving layer therefore has its own validation.

Serving checks can verify areas such as:

- expected grain
- uniqueness
- row counts
- aggregation behavior
- date ranges
- metric consistency
- output structure

The documented reference version includes **38 serving checks**.

These are not software tests and are not Data Quality rules.

They validate the analytical outputs prepared for downstream BI consumption.

---

## 18. Do Not Combine the Validation Counts

The project deliberately avoids statements such as:

```text
109 tests passed
```

by adding together:

```text
32 Data Quality rules
+
39 software tests
+
38 serving checks
```

These numbers describe different mechanisms.

Combining them would hide their meaning.

Instead, they are presented separately:

| Reliability Layer | Purpose |
|---|---|
| Software Tests | Validate implementation behavior |
| Data Quality Rules | Validate loaded business state |
| Serving Checks | Validate analytical outputs |
| Reconciliation | Compare expected source-to-target results |
| Database Constraints | Enforce persisted integrity |
| Pre-Load Validation | Prevent invalid input from entering |

This gives a clearer picture of how reliability is achieved.

---

## 19. Analytical Validation

A technically correct SQL query may still implement the wrong analytical definition.

Analytical validation therefore also considers:

- population
- grain
- denominator
- time semantics
- historical state
- exclusions
- serving grain

For example:

```text
Query Executes Successfully
        ↓
Does Not Prove
        ↓
Metric Is Analytically Correct
```

The query must still match its metric contract.

---

## 20. Dashboard Validation

The final layer is visual validation.

A serving view may be correct while Power BI still displays an incorrect result because of:

- filter context
- wrong aggregation
- percentage formatting
- cross-filtering
- snapshot handling
- unintended slicer behavior

The validation chain therefore continues into the dashboard.

```text
Correct Data
     ↓
Correct Metric
     ↓
Correct Serving Output
     ↓
Correct Visual Configuration
```

All four matter.

---

## 21. Run History and Observability

Reliability also requires knowing what happened during execution.

The project records persistent run history rather than relying only on temporary console output.

Execution metadata can include:

- run UUID
- batch identifier
- mode
- timestamps
- outcome
- status
- failure information

This supports questions such as:

```text
What ran?
When?
Against which batch?
Did it succeed?
Was it skipped?
Did an earlier attempt fail?
```

This is a lightweight local observability mechanism rather than a production monitoring platform.

---

## 22. Claim to Evidence

An important documentation principle for the repository is:

> Claims should be connected to evidence.

For example:

```text
Claim
"39 software tests"

        ↓

Evidence
Test suite
+
Reference test result
```

or:

```text
Claim
"2,903,577 raw records"

        ↓

Evidence
Source contract
+
Integrity / reconciliation output
```

The repository therefore includes an evidence layer intended to connect public claims to:

- implementation
- reference outputs
- validation results
- release version

This prevents the portfolio from relying only on unsupported statements.

---

## 23. Evidence Layers

Reference evidence will be organized by area.

Conceptually:

```text
evidence/
│
├── pipeline
│
├── schema
│
├── analytics
│
├── serving
│
└── release-validation
```

The goal is not to publish every historical log.

The goal is to preserve enough evidence to verify important public claims.

---

## 24. Historical Evidence vs Current Verification

The project contains historical evidence from successful local development runs.

However:

```text
Historical Successful Run
        ≠
Fresh Clean-Machine Reproduction
```

Before the public release, the repository will distinguish between:

- historically documented results
- current verified results
- claims revalidated during release preparation

This distinction is important for reproducibility and transparency.

---

## 25. Reproducibility and Reliability

Reliability and reproducibility are related but different.

Reliability asks:

> Does the system behave correctly?

Reproducibility asks:

> Can another environment reproduce the documented process and results?

The project currently has strong historical execution evidence.

The final publication process will also verify:

- dependencies
- setup instructions
- source package
- SQL setup
- pipeline commands
- expected outputs

Detailed reproducibility documentation is available in:

[Reproducibility](../deep-dive/reproducibility.md)

---

## 26. AI-Assisted Verification

AI was used extensively during the implementation and verification process.

Assistance included:

- generating test cases
- creating pytest implementations
- suggesting edge cases
- writing validation logic
- creating Data Quality rules
- generating reconciliation SQL
- debugging failures
- interpreting unexpected outputs
- proposing additional checks

The verification process remained iterative.

```text
Concern / Requirement
        ↓
AI-Assisted Check or Test
        ↓
Local Execution
        ↓
PASS / FAIL / Unexpected Result
        ↓
Review
        ↓
Correction
        ↓
Run Again
```

A test generated by AI is not treated as evidence simply because it exists.

The evidence comes from:

- execution
- observed behavior
- review
- correction
- validated result

More detail is available in:

[AI-Assisted Development](../deep-dive/ai_assisted_development.md)

---

## 27. What Reliability Demonstrates

The reliability layer demonstrates more than the ability to write tests.

It shows that the project considered:

```text
What if the input is wrong?

What if the same event arrives twice?

What if the same ID arrives with different data?

What if the load fails halfway?

What if the same batch runs again?

What if the database state is inconsistent?

What if the SQL result has the wrong grain?

What if Power BI changes the metric through filtering?
```

These questions represent different failure modes.

The platform attempts to address them at the layer where they belong.

---

## 28. Reliability and Business Trust

Reliability ultimately matters because analytics are used to support interpretation.

If the underlying data is unreliable, a polished dashboard can create false confidence.

The intended chain is therefore:

```text
Reliable Source Handling
        ↓
Reliable Database State
        ↓
Reliable Analytical Logic
        ↓
Reliable Serving Output
        ↓
Interpretable Dashboard
        ↓
Better Evidence for Business Discussion
```

Reliability is therefore not only a technical concern.

It supports trust in the information being presented.

---

## 29. Related Documentation

### Core Story

- [Business & Data Model](01_business_and_data_model.md)
- [Data Platform](02_data_platform.md)
- [Analytics](03_analytics.md)
- [Dashboard & Storytelling](04_dashboard_and_storytelling.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [Reproducibility](../deep-dive/reproducibility.md)
- [AI-Assisted Development](../deep-dive/ai_assisted_development.md)

### Reference

- [Data Lineage](../reference/data_lineage.md)
- [Metric Reference](../reference/metric_reference.md)
- [Schema Reference](../reference/schema_reference.md)

---

## Current Documentation Status

The reliability strategy and validation layers are documented here.

The final public repository will connect the documented test counts, Data Quality rules, reconciliation results and serving checks to the corresponding implementation and reference evidence after canonical source selection and release verification.