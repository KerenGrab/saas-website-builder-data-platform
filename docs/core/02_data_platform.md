# Data Platform

This section explains how the modeled business data was transformed into a reliable local data platform.

The goal was not only to move files into PostgreSQL.

The platform was designed to:

- understand the expected input
- validate data before writing
- transform values consistently
- respect table dependencies
- load data atomically
- distinguish duplicate delivery from conflicting data
- support safe reruns
- record execution history
- validate the resulting database state

The overall flow is:

```text
Synthetic Source Data
        ↓
Ingestion
        ↓
Validation
        ↓
Transformation
        ↓
Dependency-Aware Loading
        ↓
PostgreSQL
        ↓
Data Quality
        ↓
Run History & Evidence
```

---

## 1. Platform Architecture

The project uses a local batch-oriented architecture.

At a high level:

```text
Synthetic Sources
      ↓
Input Contract
      ↓
Python Pipeline
      ↓
Validation
      ↓
Transformation
      ↓
Load Planning
      ↓
Transactional PostgreSQL Load
      ↓
Post-Load Data Quality
      ↓
Analytical & Serving Layers
```

The platform was designed around several core principles:

- validation before database writes
- dependency-aware loading
- transactional safety
- explicit duplicate handling
- rerun awareness
- persistent execution history
- traceability between input and result

The implementation is local rather than cloud-based and is intended as a portfolio data platform rather than a production deployment.

---

## 2. Source Data Layer

The project uses a frozen synthetic input package designed to simulate realistic SaaS source systems.

The documented source package contains **49 datasets** organized across several business areas.

The main source families are:

```text
Core Product
Event Tracking
Billing & Payment
Support
```

The source package contains both CSV and JSONL files.

Each dataset is associated with expectations such as:

- expected structure
- required fields
- identifiers
- relationships
- row counts
- integrity expectations
- source fingerprints / checksums

The frozen input package is used as the reference dataset for reproducible project results.

Detailed source contracts and publication strategy are documented separately under:

[Data Documentation](../../data/README.md)

---

## 3. Ingestion

The ingestion layer is responsible for reading the source files and preparing them for validation.

The system handles multiple file formats rather than assuming a single source representation.

The ingestion process separates:

```text
File Discovery
      ↓
Source Identification
      ↓
File Reading
      ↓
Structural Inspection
      ↓
Validation
```

This separation makes it possible to detect input problems before the database is modified.

---

## 4. Validation Before Load

One of the main engineering decisions in the project was:

> Validate first. Write later.

The pipeline performs validation before business data is written to PostgreSQL.

Validation includes checks related to:

- file structure
- required columns
- expected data types
- missing values
- allowed values
- identifier structure
- relationships between datasets
- source integrity

The purpose of this layer is to answer:

> Can this input safely enter the system?

If validation fails, the load should stop before modifying the database.

This is different from post-load Data Quality, which asks whether the resulting database state is logically and analytically sensible.

---

## 5. Transformation

After validation, data is transformed into the representation expected by the database.

Transformation responsibilities include:

- type conversion
- timestamp parsing
- identifier handling
- normalization
- mapping source values to database-compatible values
- preparing historical fields
- applying controlled deduplication rules

Transformation is treated as a separate concern from validation.

```text
Validation
    ↓
"Is the source acceptable?"

Transformation
    ↓
"How should valid source data be represented for loading?"
```

---

## 6. Dependency-Aware Loading

The relational model contains many foreign-key relationships.

This means tables cannot be loaded in arbitrary order.

For example:

```text
Parent
  ↓
Child
  ↓
Dependent Child
```

The pipeline therefore builds and follows a dependency-aware load plan.

The basic principle is:

```text
Independent / Parent Tables
          ↓
Dependent Tables
          ↓
More Dependent Tables
```

This reduces foreign-key failures and makes the loading process consistent with the logical model.

The load order is derived from the structure of the data model rather than from filename order.

---

## 7. PostgreSQL Implementation

PostgreSQL is the persistence layer of the project.

The database is responsible for storing the operational model and enforcing important integrity rules.

The implementation includes database-level mechanisms such as:

- primary keys
- foreign keys
- unique constraints
- check constraints
- historical consistency rules
- operational metadata

This creates two levels of protection:

```text
Python Pipeline
      ↓
prevents invalid input from being loaded

PostgreSQL
      ↓
enforces structural and relational integrity
```

The business meaning of the model is explained in:

[Business & Data Model](01_business_and_data_model.md)

The database implementation itself is documented here as part of the platform.

---

## 8. Transactional Loading

A major reliability requirement is to avoid partial business state.

A batch should not leave the database in a situation where some related tables were updated and others were not.

The loading process therefore follows an atomic pattern:

```text
BEGIN
  ↓
Load Multiple Related Tables
  ↓
All Steps Successful?
  ├── Yes → COMMIT
  └── No  → ROLLBACK
```

The goal is:

> Either the business load succeeds as one consistent unit, or the database returns to the previous valid state.

This is especially important in a multi-table relational model.

---

## 9. Duplicate Delivery vs Data Conflict

Event-style source systems may deliver the same event more than once.

The project distinguishes between two cases.

### Identical Duplicate Delivery

```text
same event_id
+
same payload
=
repeated delivery
```

This can be treated as a safe duplicate.

The duplicate can be skipped without changing the business meaning of the data.

### Conflicting Duplicate

```text
same event_id
+
different payload
=
data conflict
```

This is not treated as a harmless duplicate.

The pipeline stops rather than silently choosing one version.

This distinction is important because:

> duplicate delivery is an operational condition; conflicting payload is a data integrity problem.

---

## 10. Rerun Semantics

Data pipelines are not expected to run only once.

A batch may need to be executed again because of:

- failures
- environment issues
- retries
- verification
- operational reruns

The project therefore defines explicit rerun behavior.

The documented logic is:

```text
Same batch_id
+
Same fingerprint
        ↓
SKIP

Same batch_id
+
Different fingerprint
        ↓
STOP
```

This prevents the system from silently treating changed data as if it were the same previously processed batch.

The goal is not generic incremental processing for every possible future source.

The current implementation is specifically designed around the documented reference input and rerun semantics.

---

## 11. Batch Identity vs Run Identity

The project separates two different concepts.

### Batch Identity

Represents the logical unit of source data being processed.

### Run Identity

Represents a specific execution attempt.

This means the same logical batch can potentially be associated with more than one execution attempt.

```text
Logical Batch
    │
    ├── Run Attempt 1
    ├── Run Attempt 2
    └── Run Attempt 3
```

This distinction improves traceability.

It allows the project to answer questions such as:

- Was this batch already processed?
- Was it skipped?
- Did an earlier run fail?
- Which execution produced the current result?

---

## 12. Run History & Observability

The pipeline records execution history rather than relying only on console output.

Run history can capture information such as:

- run identifier
- batch identifier
- execution mode
- start time
- end time
- outcome
- failure state
- processing status

This provides a basic observability layer for the local project.

The goal is not to reproduce a full production monitoring platform.

Instead, it provides enough execution history to understand what happened during a pipeline run and to connect results back to a specific execution.

---

## 13. Data Quality Layer

Validation and Data Quality are deliberately separated.

### Validation

Asks:

> Is the input structurally and logically acceptable before loading?

### Data Quality

Asks:

> After the load, does the resulting database state make sense?

Examples of post-load concerns include:

- broken business relationships
- inconsistent states
- invalid historical conditions
- unexpected population counts
- reconciliation failures

The project contains a dedicated Data Quality layer that runs after the data has been loaded.

Detailed validation evidence is documented in:

[Reliability & Validation](05_reliability_and_validation.md)

---

## 14. Reconciliation

A successful load is not enough.

The platform also needs to determine whether the result matches expectations.

Reconciliation compares the source and target states.

Conceptually:

```text
Source Records
      ↓
Expected Transformations
      ↓
Expected Duplicate Handling
      ↓
Target Records
      ↓
Compare
```

This is especially important when source duplicate deliveries exist.

A lower target row count does not automatically mean data was lost.

The difference must be explained by documented transformation or deduplication logic.

---

## 15. Pipeline Modes

The implementation supports multiple modes used during development and validation.

The documented project workflow includes commands for activities such as:

```text
plan-check
transform-check
target-check
validate
dq
```

Different modes allow the system to test specific parts of the pipeline without always performing a complete load.

This improves development and debugging by separating:

- planning
- transformation
- target inspection
- validation
- post-load Data Quality

The documented command set reflects the selected and verified canonical pipeline implementation.

---

## 16. Technical Separation of Responsibilities

The pipeline was designed as multiple modules rather than one large script.

The documented responsibilities include areas such as:

| Responsibility | Purpose |
|---|---|
| Configuration | Environment and runtime settings |
| Paths | Source and project path handling |
| Metadata | Dataset definitions and input metadata |
| Ingestion | Reading source files |
| Validation | Pre-load validation |
| Integrity | Cross-source relationship checks |
| Transformation | Source-to-target conversion |
| Load Planning | Dependency-aware ordering |
| Loading | Database writes |
| Database Access | PostgreSQL interaction |
| Rerun Logic | Batch rerun semantics |
| Data Quality | Post-load validation |
| Logging | Execution logging |
| Run History | Persistent execution metadata |

The documented module responsibilities reflect the selected canonical pipeline implementation.

---

## 17. Human-Directed, Strongly AI-Assisted Implementation

The technical implementation of the data platform was strongly AI-assisted.

AI was used extensively to accelerate work such as:

- Python implementation
- pipeline architecture exploration
- SQL generation
- validation logic
- dependency handling
- duplicate handling
- rerun behavior
- test creation
- debugging
- technical documentation

The workflow was not:

```text
Prompt
  ↓
Generated Code
  ↓
Accepted Without Review
```

Instead, development followed an iterative process:

```text
Requirement
      ↓
Discussion & Clarification
      ↓
AI-Assisted Implementation
      ↓
Local Execution
      ↓
Observed Output / Error
      ↓
Review & Discussion
      ↓
Correction
      ↓
Run Again
      ↓
Validated Behavior
```

System requirements, local execution, review of outputs and iterative decisions remained part of the development process.

The project was also a hands-on learning process.

The pipeline was used to develop practical understanding of concepts such as:

- batch processing
- validation-before-load
- database dependencies
- atomic transactions
- rollback
- idempotent behavior
- reruns
- observability

A detailed explanation of this workflow is available in:

[AI-Assisted Development](../deep-dive/ai_assisted_development.md)

---

## 18. Platform Boundaries

The current platform should be described according to what was actually implemented.

It is:

- local
- batch-oriented
- PostgreSQL-based
- Python-driven
- built around a frozen synthetic source package
- designed for portfolio-scale reproducibility

It is not currently presented as:

- a cloud deployment
- a streaming production platform
- a general-purpose orchestration framework
- an automatically scaling system
- a fully productionized SaaS backend

These are possible future directions, not current implementation claims.

---

## 19. From Platform to Analytics

The database is not the final output of the project.

Once the operational data is loaded and validated, it becomes the foundation for analytical work.

```text
Synthetic Sources
        ↓
Data Pipeline
        ↓
PostgreSQL Operational Model
        ↓
Analytical Logic
        ↓
Metric Contracts
        ↓
Serving Views
        ↓
Power BI
```

The next section explains how business questions are translated into analytical grains, populations, metrics and SQL.

[Continue to Analytics](03_analytics.md)

---

## 20. Related Documentation

### Core Story

- [Business & Data Model](01_business_and_data_model.md)
- [Analytics](03_analytics.md)
- [Dashboard & Storytelling](04_dashboard_and_storytelling.md)
- [Reliability & Validation](05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [Reproducibility](../deep-dive/reproducibility.md)
- [AI-Assisted Development](../deep-dive/ai_assisted_development.md)

### Reference

- [Data Lineage](../reference/data_lineage.md)
- [Schema Reference](../reference/schema_reference.md)

---

## Current Documentation Status

The platform architecture and engineering behavior are documented here.

The canonical Python implementation and reproducibility guidance are maintained in the repository; this document focuses on the platform architecture and engineering behavior.
