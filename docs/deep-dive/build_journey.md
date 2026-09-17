# Build Journey

This document describes how the project evolved from an initial business concept into an end-to-end Data Engineering & Analytics portfolio project.

The purpose is not to preserve every implementation step, conversation or intermediate file.

Instead, it highlights the major milestones and the points where the design changed as new business, engineering and analytical requirements became clearer.

The overall journey can be summarized as:

```text
Business Concept
        ↓
Domain Modeling
        ↓
Data Requirements
        ↓
Synthetic Source Design
        ↓
Relational Database Model
        ↓
PostgreSQL Implementation
        ↓
Python Data Pipeline
        ↓
Validation, DQ & Testing
        ↓
Analytical Modeling
        ↓
Business Analytics
        ↓
Serving Layer
        ↓
Power BI
        ↓
Portfolio Packaging
```

The final system was not designed completely in advance.

It evolved iteratively through modeling, implementation, local execution, validation and revision.

---

## 1. Starting With the Business World

The project began with a fictional but realistic business context:

> A Website Builder SaaS company needs to understand both its customers and what happens inside the Websites those customers create.

This immediately created several perspectives:

```text
SaaS Company
      ↓
Customer / Website Owner
      ↓
Website
      ↓
Visitors & Members
```

Before thinking about Python, PostgreSQL or Power BI, the project needed to answer questions such as:

```text
Who are the actors?

What does the SaaS company manage?

What does the customer manage?

What happens inside a Website?

Which activities are commercial?

Which activities are product-related?

Which activities belong to Website audiences?
```

This business framing became the foundation for the later data model.

---

## 2. From Business Actors to Domain Entities

The next stage translated the business world into conceptual entities.

Important distinctions began to emerge.

For example:

```text
Account
≠
SaaS User
≠
Website Member
≠
Visitor
```

These concepts originally appear similar because they all involve people or users.

However, they belong to different parts of the system.

Separating them early became important later when analytical populations were defined.

The project gradually expanded into concepts such as:

```text
Account
SaaS User
Website
Page
Content Item
Feature
Website Member
Visitor
Session
Interaction Event
Comment
Rating
Plan
Subscription
Payment
Support Request
```

This was the point where the fictional business began to become a structured data domain.

---

## 3. Relationships Became as Important as Entities

Once the main entities existed, the project moved beyond:

> What objects exist?

toward:

> How are those objects connected?

Examples include:

```text
Account
   ↓
owns / manages
   ↓
Website
```

and:

```text
Website
   ↓
contains
   ↓
Pages / Content
```

and:

```text
Account
   ↓
has
   ↓
Subscription / Plan History
```

Relationship modeling introduced:

- ownership
- parent-child structure
- cardinality
- lifecycle dependencies
- business rules

These relationships later influenced both database foreign keys and pipeline load order.

---

## 4. Historical Modeling Became Necessary

An early model based only on current state would not be sufficient for many realistic business questions.

Questions such as:

> Which Plan was active when this event occurred?

require historical context.

The model therefore evolved toward a combination of:

```text
Events
+
Historical States / Periods
```

For example:

```text
Feature Used
→ event

Plan Active
→ state over time
```

This led to historical modeling concepts such as:

```text
[valid_from, valid_to)
```

The project therefore moved from a simple static model toward a time-aware system.

This change later became essential for:

- Feature eligibility
- Subscription history
- Website live periods
- commercial status
- historical analytical populations

---

## 5. Business Questions Began Driving Data Requirements

The project did not treat the database model as an isolated technical exercise.

Analytical questions began influencing what data needed to exist.

The reasoning moved toward:

```text
Business Question
        ↓
Required Population
        ↓
Required Entities
        ↓
Required Relationships
        ↓
Required History
        ↓
Data Requirements
```

Questions around:

- conversion
- retention
- churn
- feature adoption
- website activity
- commercial movement

revealed requirements that were not always obvious from the conceptual model alone.

This created a feedback loop:

```text
Business Model
      ↓
Analytical Question
      ↓
Missing Requirement?
      ↓
Refine Model
```

---

## 6. Designing Synthetic Source Data

Because the company is fictional, there were no real operational systems to connect to.

The project therefore needed a realistic synthetic source layer.

The objective was not merely to generate random CSV files.

The synthetic data needed to preserve:

- entity relationships
- business rules
- history
- lifecycle logic
- realistic populations
- event activity
- analytical usefulness

The source design eventually became a frozen package of multiple datasets across areas such as:

```text
Core Product
Event Tracking
Billing & Payment
Support
```

This allowed later pipeline and analytics work to operate against a stable reference input.

---

## 7. Synthetic Data Required Iteration

Generating realistic data introduced its own problems.

The process required repeated inspection and correction.

Conceptually:

```text
Generate
   ↓
Inspect
   ↓
Validate
   ↓
Find Inconsistency
   ↓
Correct Logic
   ↓
Generate / Repair
   ↓
Validate Again
```

This was an important shift in the project.

The source data stopped being treated as disposable test data and became a controlled input package with its own integrity expectations.

The final frozen package became the reference input for the later pipeline and analytical work.

---

## 8. From Conceptual Model to Relational Model

The conceptual business model then evolved into a detailed relational design.

This required translating business meaning into:

- tables
- primary keys
- foreign keys
- unique constraints
- check constraints
- historical representations
- dependency relationships

The model became significantly more detailed than the original conceptual diagrams.

This evolution can be represented as:

```text
Business Concept
      ↓
Conceptual Entities
      ↓
Relationships
      ↓
Business Rules
      ↓
Historical Rules
      ↓
Logical Relational Model
```

The project therefore preserves a distinction between early conceptual diagrams and the later implementation model.

---

## 9. PostgreSQL Turned the Model Into an Enforced System

The next stage moved the design from documentation into an actual PostgreSQL database.

At this point, relationships and business rules were no longer only conceptual.

They became enforceable through mechanisms such as:

```text
PRIMARY KEY
FOREIGN KEY
UNIQUE
CHECK
```

This changed the project from:

> a designed schema

into:

> a database capable of rejecting invalid persisted states.

The database became the first major executable representation of the business model.

---

## 10. The Pipeline Began as More Than File Loading

The next challenge was loading the synthetic sources into PostgreSQL.

A simple first idea could have been:

```text
Read File
   ↓
Insert Rows
```

But the project requirements quickly made that insufficient.

The pipeline needed to answer:

```text
Is the input valid?

Are relationships consistent?

Which table must load first?

What happens if loading fails?

What happens if an event appears twice?

What happens if the pipeline runs again?

How do we know what happened during the run?
```

The pipeline therefore evolved into a multi-stage engineering system rather than a basic import script.

---

## 11. Validation Moved Before the Load

An important evolution was the decision to validate before modifying PostgreSQL.

Instead of:

```text
Read
  ↓
Load
  ↓
Discover Problem
```

the process became:

```text
Read
  ↓
Validate
  ↓
Transform
  ↓
Load
```

This helped isolate input problems from database-writing problems.

It also established the project principle:

> Invalid input should stop before business data is modified.

---

## 12. Loading Became Dependency-Aware

As the relational model grew, table order became important.

The project could no longer treat source files independently.

A child table might require a parent record to exist first.

The load process therefore evolved from simple iteration toward:

```text
Relationship Metadata
        ↓
Dependency Analysis
        ↓
Load Plan
        ↓
Parent Before Child
```

This connected the database design directly to pipeline execution.

---

## 13. Transaction Safety Was Added

Another important improvement was atomic loading.

The question became:

> What happens if the load fails after several related tables were already written?

The project introduced transactional behavior:

```text
BEGIN
  ↓
Load
  ↓
Success?
 ┌─┴─────┐
Yes      No
 ↓        ↓
COMMIT  ROLLBACK
```

This changed failure behavior from:

> cleanup may be required

to:

> the failed load should not intentionally leave a partial business state.

---

## 14. Duplicate Handling Became More Precise

Event sources introduced another important distinction.

At first, a duplicate identifier might appear to be a simple duplicate.

But two situations were identified:

```text
Same ID + Same Payload
→ duplicate delivery
```

and:

```text
Same ID + Different Payload
→ data conflict
```

These cases should not behave the same way.

The pipeline therefore evolved toward:

```text
Identical Duplicate
      ↓
Safe Skip

Conflicting Duplicate
      ↓
STOP
```

This was one of the points where operational behavior and data integrity were explicitly separated.

---

## 15. Rerun Behavior Became Explicit

Once the pipeline could run successfully, another question appeared:

> What happens when we run it again?

Rather than leaving rerun behavior implicit, the project defined explicit semantics.

```text
Same Batch
+
Same Fingerprint
        ↓
SKIP
```

versus:

```text
Same Batch
+
Different Fingerprint
        ↓
STOP
```

This made reruns predictable and prevented modified source data from silently appearing under an already-known batch identity.

---

## 16. Run History Added Observability

Console output alone was not enough to understand execution history.

The project therefore added persistent run metadata.

This introduced the distinction between:

```text
Batch Identity
```

and:

```text
Run Identity
```

The system could now represent:

```text
One Logical Batch
       ↓
Multiple Execution Attempts
```

This improved traceability and made the pipeline easier to inspect after execution.

---

## 17. Data Quality Became a Separate Layer

Once data could be loaded successfully, the project identified another problem:

> A technically successful load can still create a logically wrong database state.

This led to a separate post-load Data Quality layer.

The project now distinguished:

```text
Pre-Load Validation
        ↓
Can this data enter?

Post-Load Data Quality
        ↓
Does the database state make sense?
```

This was an important conceptual improvement because it prevented all validation concerns from being grouped together.

---

## 18. Testing Expanded Around Failure Behavior

Testing also evolved beyond checking only successful execution.

The project added tests around behavior such as:

- validation failure
- rerun handling
- duplicate handling
- rollback
- run history
- database interaction
- command behavior

The focus moved from:

> Does the code run?

toward:

> Does the system behave correctly when expected and unexpected conditions occur?

---

## 19. End-to-End Validation Closed the Platform Loop

After the individual pipeline pieces were developed, the project reached a stage where they were exercised together.

The end-to-end flow became:

```text
Source Package
      ↓
Validation
      ↓
Transformation
      ↓
Dependency-Aware Load
      ↓
PostgreSQL
      ↓
Data Quality
      ↓
Reference Result
```

This provided a stable platform for analytical work.

At this point, the operational data layer could be treated as a validated analytical foundation.

---

## 20. Analytical Modeling Started After the Operational Layer

The next stage did not jump directly from PostgreSQL to Power BI.

Instead, the project designed an analytical model.

This stage introduced explicit analytical grains such as:

```text
Account × Journey
Account × Month
Account × Feature × Month
Website × Month
Website × Feature × Month
Account × Churn Occurrence
```

The project also defined shared dimensions such as:

```text
Date
Account
Plan
Website
Feature
```

This created a bridge between the operational schema and business metrics.

---

## 21. Metrics Became Contracts

The analytics stage revealed that a metric name alone is not enough.

For example:

```text
Retention
```

does not define:

- the cohort
- the evaluation point
- the paid state
- the observation window
- the time semantics

The project therefore evolved toward explicit metric contracts.

```text
Business Question
      ↓
Population
      ↓
Grain
      ↓
Time
      ↓
Denominator
      ↓
Exclusions
      ↓
SQL
```

This became one of the main analytical principles of the project.

---

## 22. Eligibility Changed Feature Adoption

Feature Adoption was an example where analytical reasoning changed the metric design.

A simple version could have used:

```text
Users of Feature
----------------
All Accounts
```

But this would include Accounts that could not access the Feature.

The analysis evolved toward:

```text
Accounts That Adopted
---------------------
Eligible Accounts
```

This required connecting:

```text
Plan History
+
Feature Availability
+
Eligibility
+
Usage
```

This illustrates how the historical data model and analytical definitions became tightly connected.

---

## 23. Time Semantics Required More Care

Retention and other historical metrics introduced another analytical refinement.

Different time definitions could produce different valid results.

For example:

```text
Month-End
```

and:

```text
Exact Anniversary
```

answer related but not identical questions.

The project therefore moved away from treating time definitions as implementation details.

They became part of the metric contract.

---

## 24. SQL Became the Implementation of Analytical Reasoning

By this stage, SQL was no longer being treated as the starting point.

The process became:

```text
Question
   ↓
Definition
   ↓
SQL
   ↓
Validation
   ↓
Interpretation
```

Complex SQL was useful only if it implemented the correct analytical definition.

This represented a shift from query-centered analytics toward contract-centered analytics.

---

## 25. A Serving Layer Was Added Before Power BI

Another important evolution was the separation between:

```text
Analytical Logic
```

and:

```text
Dashboard Consumption
```

Rather than sending Power BI directly into many operational tables, the project introduced serving views.

```text
Operational Data
      ↓
Analytics
      ↓
Serving Layer
      ↓
Power BI
```

This helped control:

- grain
- aggregation
- denominator logic
- expected output structure

The dashboard therefore became a consumer of prepared analytical outputs rather than the place where all logic was invented.

---

## 26. The Dashboard Evolved Through Visual Validation

Power BI development was also iterative.

The process included repeated cycles such as:

```text
Create Visual
      ↓
Open Power BI
      ↓
Inspect
      ↓
Unexpected Result?
      ↓
Investigate
      ↓
Adjust
      ↓
Refresh
```

Issues included areas such as:

- filters
- percentages
- aggregation
- slicer behavior
- total cards
- snapshot context

This demonstrated that dashboard correctness cannot be validated from SQL alone.

The final presentation layer also requires inspection.

---

## 27. The Dashboard Became a Business Story

The dashboard eventually developed into three distinct analytical stories.

```text
Page 1
Customer Lifecycle & Multi-Dimensional Health

Page 2
Website Audience Activity,
Engagement & Feedback

Page 3
SaaS Product & Strategy Signals
```

The purpose shifted from:

> display metrics

toward:

> organize evidence around realistic management and product questions.

This made the dashboard the business-facing layer of the project.

---

## 28. Reliability Expanded Beyond the Pipeline

Reliability originally focused heavily on the data pipeline.

As the project grew, the validation scope expanded.

The full chain became:

```text
Source
  ↓
Pipeline
  ↓
Database
  ↓
Data Quality
  ↓
Analytics
  ↓
Serving
  ↓
Power BI
```

This led to separate mechanisms for:

- pre-load validation
- software testing
- database constraints
- Data Quality
- reconciliation
- analytical checks
- serving checks
- dashboard validation

The project therefore evolved toward layered reliability rather than a single testing phase.

---

## 29. AI Usage Also Evolved During the Project

The role of AI changed as the project progressed.

### Early Stages

AI was used heavily for:

```text
Brainstorming
+
Structuring ideas
+
Exploring business models
+
Discussing alternatives
```

### Technical Implementation

AI assistance became significantly stronger during:

```text
Python
SQL
Pipeline implementation
Testing
Validation
Debugging
```

### Analytics

The workflow often became:

```text
Business Question
      ↓
Joint Analytical Reasoning
      ↓
Metric Definition
      ↓
AI-Assisted SQL
      ↓
Local Execution
      ↓
Review
```

### Power BI

AI helped with:

```text
Page organization
Serving connections
Filter behavior
Troubleshooting
Implementation corrections
```

### Documentation

AI also helped turn the project history into structured technical documentation.

The development model therefore evolved naturally into:

> Human-Directed, Strongly AI-Assisted Engineering

rather than a fixed role division from the beginning.

---

## 30. Learning Happened Through Implementation

The project was also a learning process.

Concepts were not only studied theoretically.

They were encountered while building the system.

Examples include:

```text
Foreign-key dependencies
Transaction boundaries
Rollback
Batch identity
Reruns
Idempotent behavior
Historical modeling
Analytical grain
Metric denominators
Serving layers
Filter context
```

The repeated workflow was:

```text
Concept
   ↓
Implementation
   ↓
Execution
   ↓
Observed Behavior
   ↓
Question
   ↓
Correction
   ↓
Better Understanding
```

The project therefore documents both the resulting architecture and the reasoning developed while constructing it.

---

## 31. Portfolio Packaging Became Its Own Stage

After the technical project was largely built, a new problem appeared:

> How should a large development history become a clear public portfolio?

The raw project history contains:

- multiple versions
- old diagrams
- screenshots
- intermediate code
- local environment files
- debugging artifacts
- generated outputs
- historical documentation

Publishing everything directly would produce an archive rather than a portfolio.

The project therefore entered a dedicated packaging phase.

---

## 32. From Archive to Portfolio

The portfolio architecture was designed around three reading depths.

```text
Fast Reader
    ↓
README

Interested Reader
    ↓
Core Documentation

Technical Reader
    ↓
Deep Dive
+
Implementation
+
Reference
+
Evidence
```

The repository therefore separates:

```text
Story
Implementation
Reference
Evidence
```

rather than presenting every historical artifact equally.

---

## 33. Canonical Source Selection Comes After Portfolio Design

An important packaging decision was to avoid selecting source files before deciding what the portfolio needed to communicate.

The sequence became:

```text
Understand Project History
        ↓
Define Portfolio Story
        ↓
Design Repository Architecture
        ↓
Create Repository Skeleton
        ↓
Write Documentation Structure
        ↓
Select Canonical Artifacts
        ↓
Populate Implementation
        ↓
Verify Release
```

This prevents the public repository structure from being determined accidentally by whatever files happen to exist in the historical project folders.

---

## 34. Current Stage

The project is currently in the **portfolio packaging and publication preparation** stage.

The current repository already contains:

```text
Repository Architecture
        ↓
Core Documentation
        ↓
Deep-Dive Structure
        ↓
Reference Structure
        ↓
Evidence Structure
```

The next major activity is canonical artifact selection.

This includes selecting and cleaning:

- Python pipeline implementation
- test suite
- SQL
- schema setup
- analytical logic
- serving views
- diagrams
- Power BI project
- data contracts
- evidence outputs

---

## 35. What the Journey Demonstrates

The final project was not created through one linear implementation pass.

It evolved through repeated cycles:

```text
Design
  ↓
Build
  ↓
Run
  ↓
Inspect
  ↓
Find Problem
  ↓
Reason
  ↓
Change
  ↓
Validate
```

This process occurred at multiple levels:

```text
Business Modeling
Data Modeling
Data Generation
Pipeline Engineering
Analytics
Power BI
Documentation
```

The project should therefore be understood as an evolving system rather than a static collection of code.

---

## 36. Journey Summary

The complete development path can be summarized as:

```text
Business Idea
      ↓
Domain Model
      ↓
Historical Model
      ↓
Data Requirements
      ↓
Synthetic Sources
      ↓
Logical Relational Model
      ↓
PostgreSQL
      ↓
Python Pipeline
      ↓
Validation / DQ / Tests
      ↓
Analytical Model
      ↓
Metric Contracts
      ↓
SQL
      ↓
Serving Layer
      ↓
Power BI
      ↓
Reliability Across the Full Chain
      ↓
Portfolio Architecture
      ↓
Public Release Preparation
```

Each stage introduced new requirements that refined earlier decisions.

That evolution is a central part of the project.

---

## Related Documentation

### Core Story

- [Business & Data Model](../core/01_business_and_data_model.md)
- [Data Platform](../core/02_data_platform.md)
- [Analytics](../core/03_analytics.md)
- [Dashboard & Storytelling](../core/04_dashboard_and_storytelling.md)
- [Reliability & Validation](../core/05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](engineering_decisions.md)
- [Reproducibility](reproducibility.md)
- [AI-Assisted Development](ai_assisted_development.md)
- [Limitations & Future Roadmap](limitations_and_roadmap.md)

### Reference

- [Data Lineage](../reference/data_lineage.md)
- [Schema Reference](../reference/schema_reference.md)
- [Metric Reference](../reference/metric_reference.md)

---

## Current Documentation Status

This document captures the major development milestones and the main ways the project evolved.

Additional milestone evidence, selected historical diagrams and before/after examples may be added later when the canonical artifact set is finalized.