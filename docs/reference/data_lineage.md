# Data Lineage

This document describes how data moves through the SaaS Website Builder Data Platform.

It connects the major project layers:

```text
Business Question
        ↓
Source Data
        ↓
Python Data Pipeline
        ↓
Operational PostgreSQL
        ↓
Analytical Model / SQL
        ↓
Serving Layer
        ↓
Power BI
        ↓
Business Interpretation
```

The purpose of this document is to make analytical outputs traceable.

A dashboard metric should not exist as an isolated number.

It should be possible to understand:

```text
Where did the data come from?

How was it validated?

Where was it stored?

What analytical definition was applied?

What serving output exposed it?

Where did it appear in Power BI?
```

Canonical source contracts, the Python pipeline, operational schema, serving SQL and selected validation evidence are present. A complete cross-layer physical lineage index is not yet published.

---

# 1. What Data Lineage Means in This Project

Data lineage describes the path taken by data and analytical meaning as they move through the system.

The project contains several related forms of lineage.

```text
Source Lineage
    ↓
Where did the data originate?

Operational Lineage
    ↓
Where was it loaded?

Analytical Lineage
    ↓
How was it transformed into a metric?

Serving Lineage
    ↓
What output was exposed to BI?

Presentation Lineage
    ↓
Where was it shown?

Business Lineage
    ↓
What question does it support?
```

The project therefore treats lineage as more than:

```text
File A
→
Table B
```

The complete lineage also includes business and analytical semantics.

---

# 2. End-to-End Lineage Model

The primary project flow is:

```text
Business Context
        ↓
Data Requirements
        ↓
Synthetic Source Datasets
        ↓
Input Contracts
        ↓
Python Ingestion
        ↓
Validation
        ↓
Transformation
        ↓
Dependency-Aware Load
        ↓
PostgreSQL Operational Model
        ↓
Data Quality / Reconciliation
        ↓
Analytical Logic
        ↓
Metric Contract
        ↓
Serving Views
        ↓
Power BI Semantic Model
        ↓
Dashboard Visual
        ↓
Business Interpretation
```

Each layer has a different responsibility.

---

# 3. Business Context → Data Requirements

The lineage begins before data exists.

The first step is the business question.

For example:

```text
How quickly do customers become paid?
```

creates requirements for information related to:

```text
Account
Journey Start
Subscription / Paid State
Payment / Commercial History
Time
```

Similarly:

```text
Are customers adopting Features they are eligible to use?
```

creates requirements for:

```text
Account
Feature
Historical Plan
Eligibility
Feature Activity
Time
```

Therefore:

```text
Business Question
        ↓
Required Entities
        ↓
Required History
        ↓
Required Source Data
```

The source layer was designed to support these downstream questions.

---

# 4. Synthetic Source Layer

Because the Website Builder SaaS company is fictional, the project does not connect to real production systems.

Instead, synthetic source datasets represent realistic operational source areas.

The frozen source package contains:

```text
49 datasets

44 CSV
5 JSONL
```

with approximately:

```text
2.9 million raw records
```

The main source families can be understood conceptually as:

```text
Core Product
Event Tracking
Billing & Payment
Support
```

Source contracts are present under data/contracts/. The full frozen source package is published through the [data-v1.0 GitHub Release](https://github.com/KerenGrab/saas-website-builder-data-platform/releases/tag/data-v1.0), outside normal Git history. The release includes the ZIP archive and its SHA256 checksum.

---

# 5. Source Family: Core Product

Core Product sources represent relatively structured business entities and product state.

They may provide data related to concepts such as:

```text
Accounts
SaaS Users
Websites
Pages
Content
Members
Plans
Features
```

These sources form much of the structural foundation of the operational database.

Conceptual lineage:

```text
Core Product Sources
        ↓
Structural Validation
        ↓
Operational Entity Tables
        ↓
Customer / Website / Feature Analytics
```

---

# 6. Source Family: Event Tracking

Event sources represent actions occurring over time.

Examples conceptually include:

```text
Page Views
Form Submissions
Friction Events
Feature Activity
```

These sources differ from static or historical-state datasets because each row generally represents something that happened.

Conceptual lineage:

```text
Event Source
      ↓
Event Validation
      ↓
Duplicate / Conflict Handling
      ↓
Operational Event Data
      ↓
Activity Aggregation
      ↓
Analytics
```

---

# 7. Source Family: Billing & Payment

Billing and commercial sources represent customer commercial behavior.

They support concepts such as:

```text
Plan
Subscription
Payment
Commercial Transition
Paid State
```

Conceptual lineage:

```text
Billing / Payment Sources
        ↓
Operational Commercial History
        ↓
Historical Commercial State
        ↓
Conversion / Retention / Churn
```

---

# 8. Source Family: Support

Support sources represent customer-support activity.

Conceptual lineage:

```text
Support Source
      ↓
Support Records
      ↓
Operational Database
      ↓
Support Metrics / Context
      ↓
Product & Strategy Analysis
```

Support activity is treated as a contextual business signal rather than a complete customer-health definition.

---

# 9. Source Contracts

Before data enters PostgreSQL, each source is expected to follow a defined contract.

Conceptually, a contract may describe:

```text
Expected File
Expected Columns
Expected Types
Allowed Values
Keys
Relationships
Integrity Expectations
```

The lineage therefore includes:

```text
Source Dataset
      ↓
Source Contract
      ↓
Validation
```

This creates an explicit boundary between generated source data and accepted pipeline input.

---

# 10. Source Integrity

The project also records source integrity information.

A source package can be associated with:

```text
Counts
Checksums
Fingerprints
```

These help answer:

> Is this the same input package used by the reference project run?

The release archive and its SHA256 checksum are published under data-v1.0. See [Data](../../data/README.md) for download and integrity-verification instructions.

---

# 11. Pipeline Entry

Validated source files enter the Python pipeline.

At a high level:

```text
Source Files
     ↓
Ingestion
     ↓
Validation
     ↓
Transformation
     ↓
Load
```

However, each of these stages has a distinct role.

---

# 12. Ingestion Lineage

Ingestion is responsible for identifying and reading source data.

Conceptually:

```text
Source Dataset
      ↓
Pipeline Metadata
      ↓
Reader
      ↓
In-Memory Representation
```

The canonical entry point is run_pipeline.py, with the pipeline implementation under pipeline/. A complete dataset-to-module mapping remains to be documented.

---

# 13. Validation Lineage

Validation happens before PostgreSQL is modified.

The central lineage is:

```text
Source Data
      ↓
Structural Validation
      ↓
Value Validation
      ↓
Relationship Validation
      ↓
Accepted?
   ┌────┴────┐
  Yes        No
   ↓          ↓
Transform    STOP
```

This ensures that invalid source input does not silently flow further through the system.

---

# 14. Transformation Lineage

Transformation converts accepted source representations into values appropriate for the target database.

Typical transformation responsibilities include:

```text
Type Conversion
Timestamp Handling
Normalization
Historical Representation
Controlled Deduplication
```

Conceptually:

```text
Validated Source Record
        ↓
Transformation Logic
        ↓
Target-Compatible Record
```

The canonical Python implementation is present. Detailed per-dataset transformation mappings remain to be documented.

---

# 15. Duplicate-Handling Lineage

Event data introduces an important branch.

```text
Incoming Event
      ↓
Existing Event Identity?
   ┌──────┴───────┐
  No              Yes
   ↓                ↓
Load          Compare Payload
                    ↓
             ┌──────┴──────┐
          Same           Different
            ↓                ↓
          Skip             STOP
```

Therefore:

```text
Duplicate Delivery
≠
Conflicting Duplicate
```

This distinction affects source-to-target reconciliation.

---

# 16. Source-to-Target Row Lineage

The frozen reference package historically contains:

```text
Raw source rows:
2,903,577

Identical duplicate deliveries:
3,638

Expected target rows after deduplication:
2,899,939
```

Therefore the expected lineage is not:

```text
1 Source Row
=
1 Target Row
```

for every source record.

Instead:

```text
Raw Source
      ↓
Documented Deduplication
      ↓
Expected Target
```

The documented source-to-target reconciliation is available in [End-to-End Reproduction Evidence](../../evidence/release-validation/end_to_end_reproduction.md).

---

# 17. Dependency-Aware Load Lineage

Operational tables cannot be loaded in arbitrary order.

Relational dependencies influence execution.

Conceptually:

```text
Parent Entity
      ↓
Child Entity
      ↓
Dependent Entity
```

The pipeline derives or uses a load plan that respects those relationships.

Therefore:

```text
Schema Dependency
        ↓
Pipeline Dependency
```

The operational model directly affects pipeline lineage.

---

# 18. Transactional Load Lineage

The load process is executed transactionally.

Conceptually:

```text
Validated Batch
      ↓
BEGIN
      ↓
Load Tables
      ↓
Success?
  ┌────┴────┐
 Yes        No
  ↓          ↓
COMMIT    ROLLBACK
```

This means failed pipeline execution should not intentionally create a partially loaded logical batch.

---

# 19. Rerun Lineage

A rerun does not automatically create another copy of the same business data.

The reference behavior includes:

```text
batch_id
+
fingerprint
```

Decision logic:

```text
Same Batch
+
Same Fingerprint
        ↓
SKIP
```

```text
Same Batch
+
Different Fingerprint
        ↓
STOP
```

Therefore pipeline lineage also includes the relationship between:

```text
Logical Batch
        ↓
Execution Runs
```

---

# 20. Run-History Lineage

Each execution attempt receives its own execution identity.

Conceptually:

```text
Batch
  │
  ├── Run A
  ├── Run B
  └── Run C
```

Run history records operational context around execution.

This creates a traceable path between:

```text
Input Batch
      ↓
Pipeline Run
      ↓
Outcome
```

---

# 21. Operational PostgreSQL Layer

After successful loading, data exists in the operational PostgreSQL model.

Historical project documentation records:

```text
49 tables
202 documented columns
```

The physical operational schema includes concepts such as:

```text
PK
FK
UNIQUE
CHECK
Historical Structures
Operational Metadata
```

The canonical operational schema is present in sql/10_schema/001_operational_schema.sql. A consolidated source-to-table lineage table remains to be completed.

---

# 22. Source → Operational Mapping

The remaining consolidated physical lineage should use mappings in the following form:

| Source Dataset | Transformation | Target Table | Load Order | Notes |
|---|---|---|---|---|
| `<source>` | `<logic>` | `<table>` | `<n>` | `<notes>` |

This table will be generated or verified from canonical contracts, pipeline metadata and DDL.

It will not be reconstructed from historical memory alone.

---

# 23. Database Constraints as a Lineage Boundary

The PostgreSQL layer acts as another validation boundary.

```text
Transformed Record
       ↓
Database Constraint
       ↓
Persisted Record
```

A record accepted by Python must still satisfy database rules.

This gives the project multiple layers of protection rather than one validation point.

---

# 24. Post-Load Data Quality

After loading, the pipeline evaluates the resulting database state.

Conceptually:

```text
Loaded PostgreSQL
       ↓
DQ Rules
       ↓
Business / Relational Consistency
```

The historical project contains a dedicated Data Quality rule set.

These checks answer:

> Does the loaded state make sense?

rather than:

> Could the file be parsed?

---

# 25. Reconciliation Lineage

Reconciliation connects source expectations to persisted database results.

Typical flow:

```text
Raw Source
      ↓
Expected Transformations
      ↓
Expected Deduplication
      ↓
Expected Target Counts
      ↓
Actual PostgreSQL Counts
      ↓
Compare
```

This provides evidence that the pipeline did not silently lose or duplicate data.

---

# 26. Operational → Analytical Lineage

The next transition changes the purpose of the data.

Operational data represents the business system.

Analytical structures represent business questions.

Conceptually:

```text
Operational Tables
       ↓
Business Question
       ↓
Population
       ↓
Grain
       ↓
Historical Logic
       ↓
Metric Contract
       ↓
Analytical SQL
```

This is not a direct table-copy process.

---

# 27. Analytical Model

The project contains seven documented analytical fact designs.

```text
First Paid Conversion Journey
Product Activity Snapshot
Commercial Status Snapshot
Paid Churn Occurrence
Account Feature Activity Snapshot
Website Outcomes Snapshot
Website Feature Activity Snapshot
```

Shared dimensions include:

```text
Date
Account
Plan
Website
Feature
```

These are analytical designs and should not automatically be interpreted as seven materialized physical PostgreSQL fact tables.

---

# 28. Analytical Grain Lineage

Each analytical path has a defined grain.

Examples:

```text
Account × Journey

Account × Month

Account × Churn Occurrence

Account × Feature × Month

Website × Month

Website × Feature × Month
```

Lineage must preserve grain.

Otherwise:

```text
Correct Source Data
+
Wrong Join / Aggregation
=
Incorrect Metric
```

---

# 29. Metric-Contract Lineage

The analytical definition sits between raw data and SQL.

```text
Business Question
        ↓
Population
        ↓
Grain
        ↓
Time Semantics
        ↓
Denominator
        ↓
Metric Contract
        ↓
SQL
```

The SQL is therefore an implementation of an analytical definition.

It is not the definition by itself.

---

# 30. Analytical SQL Lineage

A complete analytical implementation index should use fields such as:

| Metric / Model | Operational Inputs | SQL File | Output Grain | Notes |
|---|---|---|---|---|
| `<metric>` | `<tables>` | `<sql>` | `<grain>` | `<notes>` |

Standalone analytical SQL is not yet published under sql/30_analytics. Exact metric-to-implementation mappings remain outstanding.

---

# 31. Analytical → Serving Lineage

Power BI does not consume every operational or analytical structure directly.

A serving layer sits between analytics and reporting.

```text
Operational Database
        ↓
Analytical Logic
        ↓
Serving Views
        ↓
Power BI
```

This layer prepares outputs specifically for downstream consumption.

---

# 32. Why the Serving Layer Exists

The serving layer can control:

```text
Grain
Aggregation
Naming
Denominators
Date Context
Expected Output Shape
```

This prevents important analytical logic from being recreated independently inside individual Power BI visuals.

---

# 33. Serving Validation

Serving outputs are validated separately from:

```text
Software Tests
```

and:

```text
Data Quality Rules
```

Representative serving validation may check:

```text
Expected Grain
Uniqueness
Date Ranges
Row Counts
Aggregation
Metric Consistency
```

The historical project includes:

```text
12 serving views
38 serving checks
```

The canonical serving SQL is present in sql/40_serving/001_dashboard_views.sql. The 38-check count refers to historical serving-validation evidence and should not be presented as a fresh-clone verification result.

---

# 34. Serving → Power BI Lineage

Conceptually:

```text
Serving View
      ↓
Power BI Semantic Model
      ↓
Measure / Field
      ↓
Visual
      ↓
Dashboard Page
```

The final lineage reference will map each important dashboard visual back to its serving source.

---

# 35. Power BI Pages

The project contains three business-oriented dashboard pages.

```text
Page 1
Customer Lifecycle & Multi-Dimensional Health
```

```text
Page 2
Website Audience Activity,
Engagement & Feedback
```

```text
Page 3
SaaS Product & Strategy Signals
```

These pages represent different analytical stories rather than arbitrary visual groupings.

---

# 36. Golden Path: First Paid Conversion

The first major lineage path is:

```text
Business Question
How quickly do eligible Accounts become paid?

        ↓

Customer / Commercial Source Data

        ↓

Operational Account
+
Subscription / Payment / Commercial History

        ↓

Eligible Journey Population

        ↓

Account × Journey Analytical Grain

        ↓

First Qualifying Paid Event

        ↓

30 / 60 / 90 / 180 Day Horizons

        ↓

Conversion Metric

        ↓

Serving Output

        ↓

Power BI
Customer Lifecycle Page

        ↓

Business Interpretation
```

The source contracts, physical schema and serving SQL are available. A consolidated physical mapping for this Golden Path remains to be completed.

---

# 37. Golden Path: Paid Retention

```text
Business Question
Do paid Accounts remain paid?

        ↓

Commercial Source Data

        ↓

Operational Subscription /
Commercial History

        ↓

Paid Entry Cohort

        ↓

Historical Paid State

        ↓

M1 / M3 / M6 / M12 Evaluation

        ↓

Paid Retention

        ↓

Serving Output

        ↓

Power BI
Customer Lifecycle Page

        ↓

Retention Interpretation
```

A key lineage dependency is historical commercial state.

Current Account state alone is not sufficient.

---

# 38. Golden Path: Product vs Paid Activity

```text
Business Question
Does commercial status align
with product engagement?

        ↓

Product Activity Sources
+
Commercial Sources

        ↓

Operational Events
+
Historical Commercial State

        ↓

Account × Month

        ↓

Product Activity
+
Paid Status

        ↓

Combined State

        ↓

Serving Output

        ↓

Power BI
Customer Lifecycle Page

        ↓

Mismatch Investigation
```

The important lineage rule is:

```text
Product Activity Time
=
Commercial Status Time
```

Historical periods must be aligned.

---

# 39. Golden Path: Feature Adoption

```text
Business Question
Are Accounts using Features
they had access to?

        ↓

Feature Definitions
+
Plan History
+
Feature Activity

        ↓

Operational Feature /
Commercial Structures

        ↓

Historical Eligibility

        ↓

Account × Feature × Month

        ↓

Eligible?
        ↓
Used?

        ↓

Adoption Metric

        ↓

Serving Output

        ↓

Power BI

        ↓

Product Interpretation
```

This path demonstrates why:

```text
Usage
alone
```

is not enough.

Eligibility is part of the metric lineage.

---

# 40. Golden Path: Website Outcomes

```text
Business Question
What is happening on customer Websites?

        ↓

Website Structure
+
Visitor Activity
+
Sessions
+
Interaction Events
+
Comments
+
Ratings

        ↓

Operational Website /
Audience Data

        ↓

Website × Month

        ↓

Sessions
Page Views
Forms
Friction
Engagement
Feedback

        ↓

Serving Outputs

        ↓

Power BI
Website Audience Page

        ↓

Website-Level Interpretation
```

This path combines behavioral and explicit-feedback signals without collapsing them into one generic success metric.

---

# 41. Golden Path: Commercial Transitions

```text
Business Question
How do Accounts move between
commercial states?

        ↓

Plan / Subscription /
Commercial History

        ↓

Operational Historical State

        ↓

Detect State Transition

        ↓

Account × Commercial Transition

        ↓

Upgrade
Downgrade
Cancellation
Reactivation

        ↓

Serving Output

        ↓

Power BI
Product & Strategy Page

        ↓

Commercial Interpretation
```

One Account may generate multiple transition events.

Therefore:

```text
Transition Count
≠
Distinct Accounts
```

---

# 42. Golden Path: Locked Feature Attempts

```text
Business Question
Are users attempting Features
they cannot currently access?

        ↓

Feature Activity
+
Eligibility / Access Context

        ↓

Operational Event Data

        ↓

Attempt
+
Access State

        ↓

Locked Attempt

        ↓

Serving Output

        ↓

Power BI
Product & Strategy Page

        ↓

Product / Packaging Investigation
```

A locked attempt is a signal.

It is not automatically evidence that a customer would purchase an upgrade.

---

# 43. Lineage Across Historical State

Many analytical paths depend on historical as-of logic.

Conceptually:

```text
Activity at Time T
        ↓
Find State Valid at Time T
        ↓
Join Historical Context
        ↓
Analyze
```

Examples include:

```text
Plan at Time T
Subscription State at Time T
Website Live State at Time T
Feature Eligibility at Time T
```

Using today's state can break analytical lineage.

---

# 44. Lineage and Partial Periods

Time coverage must also be carried through the lineage.

For example:

```text
Source Coverage
      ↓
Analytical Period
      ↓
Serving Period
      ↓
Dashboard Period
```

If the latest month is partial, that context should not disappear at the dashboard layer.

Therefore lineage includes not only values but also interpretation metadata.

---

# 45. Lineage and Grain Changes

Not every layer has the same grain.

Example:

```text
Raw Event
      ↓
Session
      ↓
Website × Month
      ↓
Dashboard Total
```

Each transformation changes what one row means.

The final lineage documentation should make those grain transitions explicit.

---

# 46. Lineage and Denominators

Rates require denominator lineage.

For example:

```text
Feature Adoption
```

should be traceable through:

```text
Eligible Population
      ↓
Adopted Population
      ↓
Rate
```

The serving layer and Power BI must not silently replace the denominator with another population.

---

# 47. Lineage and Filters

Power BI introduces another transformation context:

```text
Filter
      ↓
Semantic Model
      ↓
Metric Evaluation
```

A dashboard filter can change the population being evaluated.

For that reason, some metrics require:

```text
Filter Isolation
```

or:

```text
Snapshot Isolation
```

to preserve their intended meaning.

---

# 48. Lineage and Evidence

Important lineage paths should ultimately connect to evidence.

The intended structure is:

```text
Business Claim
      ↓
Metric Contract
      ↓
SQL
      ↓
Serving View
      ↓
Reference Result
      ↓
Evidence Artifact
```

This allows a reader to verify more than the final dashboard number.

---

# 49. Claim-to-Lineage Mapping

The existing curated evidence can be extended into a consolidated claim-to-lineage table:

| Claim | Origin | Transformation | Final Output | Evidence |
|---|---|---|---|---|
| `<claim>` | `<source>` | `<pipeline / SQL>` | `<view / visual>` | `<artifact>` |

The implementation and evidence artifacts are present, but the consolidated claim-to-lineage table remains to be completed.

---

# 50. Planned Source-Level Lineage

Using the canonical source contracts, the repository can further document:

```text
Dataset
      ↓
Contract
      ↓
Pipeline Reader
      ↓
Transformation
      ↓
Target Table
```

This will provide physical source lineage.

---

# 51. Planned Table-Level Lineage

The canonical DDL is present. The remaining cross-layer mapping should make this path explicit:

```text
Operational Table
      ↓
Used By Analytical SQL
      ↓
Used By Serving View
      ↓
Used By Dashboard
```

can be documented explicitly.

---

# 52. Planned Column-Level Lineage

Column-level lineage is not required for every one of the documented schema columns.

It should be added selectively where it provides value.

High-value candidates include fields involved in:

```text
Historical Validity
Paid State
Feature Eligibility
Event Identity
Time
Account Identity
Website Identity
```

This keeps the public reference useful rather than excessively mechanical.

---

# 53. Planned Visual Lineage

Selected lineage paths can later be converted into diagrams.

Useful candidates include:

```text
Overall Platform Lineage

First Paid Conversion

Feature Adoption

Website Outcomes
```

The diagrams should complement this reference rather than duplicate every table and column.

---

# 54. Canonical Artifact Requirement

The final lineage must use canonical implementation artifacts.

The process is:

```text
Historical Artifact Inventory
        ↓
Canonical Selection
        ↓
Verification
        ↓
Lineage Mapping
```

If two historical SQL files implement different definitions, lineage should not point to both as if they were equally current.

---

# 55. Lineage Verification

Before publication, important lineage paths should be tested.

For example:

```text
Metric Contract
      ↓
Canonical SQL
      ↓
Serving View
      ↓
Power BI Value
```

The expected values should reconcile across the chain.

A discrepancy should be investigated rather than documented as normal.

---

# 56. Current Lineage Boundary

The current repository provides several concrete lineage anchors:

- source contracts under data/contracts/
- the canonical entry point and pipeline/ implementation
- the operational PostgreSQL schema
- dashboard-serving SQL
- the Power BI Project source
- curated pipeline, schema, analytics, serving and release evidence

The major business and analytical Golden Paths are also documented here.

However, a complete physical lineage index has not yet been assembled.
In particular, the repository still needs consolidated mappings from
source datasets to tables, analytical logic to serving outputs, selected
Power BI visuals to serving fields, and public claims to evidence.

Standalone analytical SQL is not yet published under sql/30_analytics.

The distinction is between artifacts that already exist and traceability
work that remains incomplete.

---

# 57. Final Target

The final public lineage should allow a reader to begin with a business-facing output and move backward.

For example:

```text
Power BI Metric
      ↑
Serving View
      ↑
Analytical SQL
      ↑
Metric Contract
      ↑
Operational Tables
      ↑
Pipeline
      ↑
Source Datasets
```

It should also allow the opposite direction:

```text
Source Dataset
      ↓
Pipeline
      ↓
PostgreSQL
      ↓
Analytics
      ↓
Serving
      ↓
Power BI
      ↓
Business Interpretation
```

This two-direction traceability is the target of the final lineage reference.

---

## Related Documentation

### Core

- [Business & Data Model](../core/01_business_and_data_model.md)
- [Data Platform](../core/02_data_platform.md)
- [Analytics](../core/03_analytics.md)
- [Dashboard & Storytelling](../core/04_dashboard_and_storytelling.md)
- [Reliability & Validation](../core/05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [Build Journey](../deep-dive/build_journey.md)
- [Reproducibility](../deep-dive/reproducibility.md)

### Reference

- [Glossary](glossary.md)
- [Schema Reference](schema_reference.md)
- [Metric Reference](metric_reference.md)

### Repository

- [Data](../../data/README.md)
- [SQL](../../sql/README.md)
- [Dashboard](../../dashboard/README.md)
- [Evidence](../../evidence/README.md)

---

## Current Documentation Status

The end-to-end conceptual lineage and the major analytical Golden Paths are documented here.

Canonical source contracts, pipeline code, the physical schema, serving SQL and selected evidence are present. Complete source-to-table, analytical-SQL-to-serving, visual and claim-to-evidence mappings remain release documentation tasks.
