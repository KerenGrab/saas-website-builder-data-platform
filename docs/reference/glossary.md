# Glossary

This glossary defines the main business, data-engineering, analytical and reporting terms used throughout the project.

Its purpose is to keep terminology consistent across:

```text
Business & Domain Modeling
        ↓
Data Platform
        ↓
Analytics
        ↓
Serving Layer
        ↓
Power BI
```

Terms are grouped by context rather than alphabetically so that related concepts can be understood together.

---

# 1. Business & Domain Concepts

## Account

The primary customer-level business entity in the SaaS platform.

An Account represents the organization or customer relationship using the Website Builder product.

An Account may be associated with:

- SaaS Users
- Websites
- Plans
- Subscriptions
- Payments
- Feature activity
- Support activity

Many commercial and lifecycle analyses use **Account** as their primary analytical population.

---

## SaaS User

A person who operates the Website Builder product on behalf of an Account.

A SaaS User belongs to the **customer-management side** of the platform.

It is intentionally different from a Website Member or Visitor.

```text
SaaS User
→ uses the Website Builder product

Website Member / Visitor
→ uses or visits a customer's Website
```

---

## Website

A digital property created and managed by an Account.

An Account may manage more than one Website.

Website-level analytics therefore should not automatically be interpreted as Account-level analytics.

---

## Page

A page belonging to a Website.

Pages form part of the Website structure and may generate audience activity such as page views.

---

## Content Item

A content element managed within a Website.

The exact implementation can vary according to the underlying source and relational model.

---

## Visitor

An audience identity interacting with a Website.

A Visitor does not necessarily need to be registered.

Visitors may generate:

- Sessions
- Page Views
- Interaction Events
- other Website activity

---

## Website Member

A registered or recognized user of a customer's Website.

A Website Member belongs to the **website-audience side** of the system.

It is not the same as a SaaS User.

---

## Session

A bounded period of Website activity associated with a Visitor.

Sessions are used to analyze audience behavior such as:

- visit volume
- engagement
- pages per session
- session duration
- friction

---

## Interaction Event

A recorded action occurring within the product or Website environment.

Examples may include:

```text
page_viewed
form_submitted
failure_friction
feature activity
```

Events normally represent something that happened at a particular point in time.

---

## Comment

Explicit textual feedback associated with Website activity.

Comments represent a different type of signal from behavioral activity.

---

## Rating

Structured audience feedback represented through a rating value.

Ratings are used as an explicit feedback signal rather than an implicit behavioral signal.

---

## Feature

A product capability available within the Website Builder SaaS platform.

Feature analysis may distinguish between:

```text
Available
Eligible
Enabled
Used
```

These concepts should not automatically be treated as equivalent.

---

## Plan

A commercial offering that defines part of the customer's product access and commercial context.

Plan information may change over time.

Historical analyses should therefore use the Plan that was active during the relevant period when necessary.

---

## Subscription

The commercial relationship between an Account and a SaaS Plan over time.

Subscription state may be used in:

- paid-status analysis
- retention
- churn
- reactivation
- commercial transitions

---

## Payment

A recorded financial transaction associated with the SaaS commercial relationship.

Payment activity may contribute to conversion and commercial-state analysis.

---

## Support Request

A customer-support interaction or issue.

Support activity is used as an operational and customer-friction signal.

---

# 2. Identity Distinctions

## Account vs SaaS User

```text
Account
→ customer-level organization / commercial entity

SaaS User
→ person operating the platform for that Account
```

One Account may be associated with multiple SaaS Users.

---

## SaaS User vs Website Member

```text
SaaS User
→ manages the Website Builder product

Website Member
→ belongs to the audience of a customer Website
```

These represent different populations.

---

## Website Member vs Visitor

A Website Member is a recognized or registered Website user.

A Visitor may interact with a Website without being registered.

Therefore:

```text
Website Member
≠
Visitor
```

although a person may potentially be represented in both contexts depending on system behavior.

---

# 3. Data Modeling Concepts

## Entity

A business concept represented in the data model.

Examples:

```text
Account
Website
Plan
Feature
Visitor
```

---

## Relationship

A defined connection between entities.

Examples include:

```text
Account → Website
Website → Page
Account → Subscription
```

Relationships can also define ownership and dependency.

---

## Cardinality

The number of instances of one entity that may relate to another.

Examples:

```text
one Account
→ many Websites
```

Cardinality affects both relational modeling and join behavior.

---

## Primary Key

A column or set of columns that uniquely identifies a database row.

Common notation:

```text
PK
```

---

## Foreign Key

A column or set of columns that references another table's key.

Common notation:

```text
FK
```

Foreign keys help enforce relational integrity.

---

## Unique Constraint

A database constraint requiring a value or combination of values to be unique.

---

## Check Constraint

A database rule that restricts which values or combinations are allowed.

It is one layer of persisted integrity protection.

---

## Referential Integrity

The requirement that relationships between records remain valid.

For example:

```text
Child references Parent
        ↓
Parent must exist
```

---

## Conceptual Model

A high-level representation of the business domain.

It focuses on questions such as:

- what exists?
- who interacts?
- who owns what?
- what relationships matter?

It is not intended to show every physical table or column.

---

## Logical Relational Model

A more detailed representation of the data model containing relational structures such as:

- tables
- keys
- relationships
- historical structures
- constraints

The project documentation distinguishes this model from earlier conceptual ERDs.

---

## Physical Database Model

The implemented PostgreSQL representation of the logical design.

This is where abstract rules become concrete database structures and constraints.

---

# 4. Historical Modeling

## Event

Something that happens at a particular point in time.

Conceptually:

```text
---------●----------→ time
```

Examples:

- Payment completed
- Page viewed
- Feature used
- Commercial transition

---

## State

A condition that remains true over a period.

Examples:

- Account is on a Plan
- Website is live
- Subscription is active

---

## Historical Period

A representation of when a state is valid.

Common conceptual structure:

```text
valid_from
valid_to
```

---

## Half-Open Interval

A historical interval represented as:

```text
[valid_from, valid_to)
```

The starting boundary is included.

The ending boundary is excluded.

This prevents adjacent historical periods from overlapping at the boundary.

---

## Historical State

The state that existed at a particular point in the past.

For example:

```text
Which Plan was active
when this Feature event happened?
```

Historical state should not automatically be replaced with the current state.

---

## Current State

The state that exists now.

Current state is useful for present-time questions but may be incorrect for historical analysis.

---

# 5. Source Data Concepts

## Source Dataset

A file or source unit entering the data platform.

The reference source package contains multiple CSV and JSONL datasets.

---

## CSV

Comma-Separated Values.

A tabular text-file format used by many source datasets in the project.

---

## JSONL

JSON Lines.

A format where each line contains an independent JSON record.

It is useful for event-oriented datasets.

---

## Source Contract

A documented expectation describing what a source dataset should contain.

A contract may define:

- required columns
- identifiers
- formats
- relationships
- expected counts
- integrity expectations

---

## Frozen Dataset

A fixed reference version of the synthetic source package.

It is used so pipeline and analytical results can be reproduced against a stable input.

---

## Checksum

A calculated value used to verify file integrity.

If the checksum of a downloaded file differs from the published reference checksum, the file may have changed or become corrupted.

---

## Fingerprint

A value representing the identity or content of a source batch.

In the pipeline, fingerprints participate in rerun semantics.

---

# 6. Pipeline Concepts

## Data Pipeline

The system responsible for moving source data through validation, transformation and loading into the target database.

The project uses a local batch-oriented Python pipeline.

---

## Batch

A logical unit of source data processed together.

Batch identity is different from run identity.

---

## Batch ID

The identifier representing a logical input batch.

It is used when evaluating rerun behavior.

---

## Run

A single execution attempt of the pipeline.

One Batch may be associated with multiple Runs.

---

## Run ID / Run UUID

A unique identifier assigned to one pipeline execution attempt.

It supports execution traceability.

---

## Ingestion

The process of reading and identifying source data before transformation and loading.

---

## Transformation

The conversion of accepted source data into the representation required by the target database.

Examples may include:

- type conversion
- timestamp parsing
- normalization
- historical field preparation
- controlled deduplication

---

## Load

The process of writing transformed data into PostgreSQL.

---

## Dependency-Aware Loading

Loading tables according to their relational dependencies.

Conceptually:

```text
Parent
   ↓
Child
   ↓
Dependent Child
```

This helps preserve foreign-key integrity.

---

## Load Plan

The ordered sequence in which datasets or target tables should be loaded.

---

# 7. Validation & Reliability Concepts

## Validation

In this project, Validation primarily refers to checks performed **before loading**.

Its central question is:

> Can this source safely enter the system?

---

## Data Quality

Post-load checks evaluating whether the resulting database state is logically and analytically sensible.

Its central question is:

> Does the loaded database state make sense?

---

## Integrity Check

A check that evaluates whether records and relationships obey expected structural or business rules.

---

## Structural Validation

Validation related to the shape of the input.

Examples:

- required columns
- expected file
- expected format

---

## Value Validation

Validation determining whether source values are acceptable.

Examples:

- allowed categories
- non-null requirements
- valid ranges

---

## Relationship Validation

Validation of relationships across records or datasets.

Example:

```text
Child parent_id
        ↓
must reference
        ↓
existing Parent
```

---

## Reconciliation

Comparison between expected source-derived results and actual target results.

Typical flow:

```text
Source Count
    ↓
Expected Transformations
    ↓
Expected Deduplication
    ↓
Expected Target
    ↓
Actual Target
```

---

## Transaction

A group of database operations treated as one logical unit.

---

## Atomicity

The property that a transaction completes entirely or not at all.

Conceptually:

```text
All Succeed
→ COMMIT

Any Required Step Fails
→ ROLLBACK
```

---

## COMMIT

Makes the changes in a successful transaction persistent.

---

## ROLLBACK

Reverses the changes made within a failed transaction.

---

## Partial Load

A state where only part of a logically connected batch has been written successfully.

The project's transactional loading strategy is intended to avoid partial business loads.

---

# 8. Duplicate & Rerun Concepts

## Duplicate Delivery

The same logical event delivered more than once with the same payload.

Conceptually:

```text
same event_id
+
same payload
```

This can be treated as a safe redelivery under the documented duplicate policy.

---

## Conflicting Duplicate

The same event identifier appearing with different content.

Conceptually:

```text
same event_id
+
different payload
```

This is treated as a data-integrity conflict rather than a harmless duplicate.

---

## Deduplication

The controlled process of preventing repeated deliveries of the same logical record from becoming duplicate target records.

---

## Rerun

Executing the pipeline again for a logical batch.

---

## Rerun Semantics

The documented behavior of the system when a batch is processed again.

The reference policy includes:

```text
same batch_id
+
same fingerprint
→ SKIP
```

and:

```text
same batch_id
+
different fingerprint
→ STOP
```

---

## Idempotent Behavior

Behavior where safely repeating an operation does not unintentionally create additional business effects.

The project's rerun policy provides controlled idempotent behavior for known identical batches.

---

# 9. Observability Concepts

## Run History

Persistent metadata describing pipeline executions.

It may include:

- run identifier
- batch identifier
- mode
- timestamps
- status
- outcome

---

## Logging

Recorded execution messages that help explain what occurred during a pipeline run.

---

## Observability

The ability to understand system behavior from recorded execution information.

The project implements lightweight local observability through logs and run history.

It is not intended to represent a full production monitoring stack.

---

# 10. Analytical Concepts

## Business Question

The business problem an analysis is intended to answer.

Analytics in the project begin with the business question rather than with SQL.

---

## Population

The entities eligible to participate in an analysis.

Examples:

```text
Eligible Accounts
Paid Accounts
Active Websites
```

---

## Grain

The meaning of one analytical row.

Examples:

```text
Account × Month

Website × Month

Account × Feature × Month
```

Grain is defined before analytical implementation.

---

## Denominator

The base population used in a ratio or percentage.

Choosing the denominator is treated as a business and analytical decision.

---

## Numerator

The population or events counted in the top part of a ratio.

---

## Metric Contract

The explicit definition of an analytical metric.

A contract may define:

```text
Business Question
Population
Grain
Event / State
Time Definition
Denominator
Exclusions
Caveats
Output Meaning
```

---

## Analytical Model

The structured design used to organize business analytics.

The project contains multiple analytical fact designs and shared dimensions.

---

## Fact

An analytical structure describing measurable events, states or snapshots at a defined grain.

---

## Dimension

A descriptive analytical structure used to provide context to facts.

Shared dimensions in the project include concepts such as:

```text
Date
Account
Plan
Website
Feature
```

---

## Snapshot

A representation of state at a defined point or period in time.

Example:

```text
Account × Month
```

---

## Cohort

A population grouped according to a shared starting condition or event.

For example, Accounts entering paid status during the same period may form a paid cohort.

---

## Observation Window

The time period during which an entity can be observed for a metric outcome.

---

## Conversion Horizon

A defined period during which conversion is evaluated.

Examples might include:

```text
30 days
60 days
90 days
180 days
```

depending on the metric contract.

---

## Censoring

A condition where an entity has not yet had enough observation time to determine a full outcome for a particular horizon.

---

# 11. Core Analytical Metrics

## First Paid Conversion

The first qualifying transition of an eligible Account into a paid state after its defined starting point.

The exact calculation depends on its metric contract.

---

## Paid Retention

A measure of how many members of a defined paid cohort remain in the qualifying paid state at a later evaluation point.

Retention depends strongly on:

- cohort definition
- paid-state definition
- evaluation time
- observation availability

---

## Product Activity

Activity indicating meaningful use of the SaaS product.

The precise activity definition must follow the relevant metric contract.

---

## Product vs Paid Activity

An analysis comparing commercial status with product engagement.

Possible states include:

```text
Paid + Product Active

Paid + Product Inactive

Not Paid + Product Active

Not Paid + Product Inactive
```

---

## Feature Eligibility

Whether an Account had access to a Feature under the relevant business rules and historical Plan context.

---

## Feature Enablement

Whether a Feature was enabled for the relevant entity.

Eligibility and enablement are not necessarily the same concept.

---

## Feature Usage

Observed activity associated with a Feature.

---

## Feature Adoption

Use of a Feature by an eligible population under the project's defined adoption contract.

Conceptually:

```text
Adopted
--------
Eligible
```

where appropriate.

---

## Locked Feature Attempt

An attempt to use functionality that is not available under the relevant access conditions.

It is treated as a product signal rather than automatically as an upgrade decision.

---

## Paid Churn

A qualifying transition out of a paid state according to the project's churn definition.

---

## Reactivation

A transition in which an Account returns to a qualifying active or paid commercial state after leaving it.

---

## Upgrade

A commercial transition from one Plan or commercial level to a higher one according to the documented business rules.

---

## Downgrade

A commercial transition from one Plan or commercial level to a lower one.

---

## Commercial Transition

A change between commercial states or Plans.

One Account can generate multiple transition events over time.

Therefore:

```text
Transition Count
≠
Distinct Account Count
```

---

# 12. Website Analytics Concepts

## Page View

An event representing a viewed Website page.

---

## Form Submission

An interaction in which a Website visitor submits a form.

It can represent a meaningful audience action.

---

## Friction Event

An event representing failure, difficulty or unsuccessful interaction within the Website experience.

---

## Pages per Session

A Website engagement metric representing the number of page views relative to Sessions.

---

## Session Duration

A time-based engagement metric describing the duration of Website Sessions according to the implemented metric definition.

---

## Audience Activity

Behavior generated by Visitors or Website Members on customer Websites.

---

## Explicit Feedback

Feedback intentionally provided by users, such as:

```text
Comments
Ratings
```

This differs from behavioral signals such as Session activity.

---

# 13. Time Semantics

## Calendar Month

A standard calendar-based monthly period.

---

## Month-End State

The state of an entity evaluated at the end of a calendar month.

---

## Exact Anniversary

An evaluation point based on an exact elapsed interval from an entity-specific starting date rather than a calendar boundary.

---

## Partial Period

A reporting period containing less than the full expected observation duration.

Partial periods should not automatically be interpreted as directly comparable with complete periods.

---

## Time Semantics

The rules determining how time is interpreted by a metric.

Examples include:

```text
Calendar Month
Month-End
Exact Anniversary
Rolling Window
Conversion Horizon
Historical As-Of Date
```

Time semantics are part of the analytical definition.

---

# 14. Serving Layer Concepts

## Serving Layer

The controlled interface between analytical logic and downstream BI.

Conceptually:

```text
Operational Data
      ↓
Analytics
      ↓
Serving Layer
      ↓
Power BI
```

---

## Serving View

A database view designed to provide a controlled analytical output for downstream consumers such as Power BI.

---

## Analytical Grain

The grain at which underlying analytical logic is defined.

---

## Serving Grain

The grain exposed by a serving output.

It may differ from the analytical grain if explicit aggregation is required.

---

## Serving Validation

Checks used to verify serving outputs.

These may evaluate:

- expected grain
- uniqueness
- row counts
- date ranges
- aggregation behavior
- output structure
- metric consistency

Serving checks are intentionally kept separate from software tests and Data Quality rules.

---

# 15. Business Intelligence Concepts

## Power BI

The business-intelligence platform used for the final dashboard and analytical storytelling layer.

---

## Semantic Model

The Power BI model that defines the reporting data structure, relationships and analytical behavior used by report visuals.

---

## Dashboard / Report Page

A visual business-facing presentation of analytical information.

The project currently organizes the Power BI report into three analytical stories.

---

## Visual

A chart, card, table or other Power BI element used to display analytical information.

---

## Filter Context

The set of active Power BI filters influencing the calculation or visual currently being evaluated.

---

## Slicer

An interactive Power BI control used to filter report content.

---

## Filter Isolation

The intentional restriction of a filter so that it affects only the visuals for which it is analytically appropriate.

---

## Snapshot Isolation

The preservation of a metric's intended snapshot context when unrelated report filters should not redefine it.

---

# 16. Reliability Evidence Concepts

## Software Test

A test validating implementation behavior.

The historical reference implementation contains a dedicated pytest test suite.

Software tests are not the same as Data Quality rules.

---

## Data Quality Rule

A rule validating the business or relational state of loaded data.

It operates at a different layer from software tests.

---

## Serving Check

A validation targeting analytical or serving-layer output.

---

## Reference Result

A selected output representing an expected result for a documented project version.

---

## Evidence

An artifact used to support a technical or analytical claim.

Examples include:

- test output
- reconciliation output
- SQL result
- checksum
- validated reference count

---

## Claim-to-Evidence Mapping

A documentation pattern connecting a public statement to the artifact or process that verifies it.

Conceptually:

```text
Claim
  ↓
Implementation
  ↓
Evidence
```

---

# 17. Reproducibility Concepts

## Reproducibility

The ability to recreate documented project behavior or results from a defined environment and input.

---

## Result Reproduction

Reproducing documented outputs from the verified frozen dataset.

This is the primary reproducibility target for the first public release.

---

## Exact Data Regeneration

Recreating the exact synthetic source package from the data-generation process itself.

This is a separate reproducibility goal.

---

## Clean-Machine Reproduction

Running the project from a fresh environment using only documented prerequisites and published artifacts.

---

## Canonical Artifact

The selected authoritative public version of a project artifact.

Examples may include:

```text
Canonical Pipeline
Canonical SQL
Canonical ERD
Canonical Power BI Project
```

Historical alternatives are not automatically canonical.

---

## Reference Dataset

The specific frozen dataset associated with a documented project release and its expected results.

---

## Release Artifact

A file or package distributed with a project release rather than stored directly in normal Git history.

The full frozen dataset is intended to become such an artifact.

---

# 18. AI-Assisted Development Concepts

## Human-Directed, AI-Assisted Engineering

The development approach used throughout the project.

Human direction included areas such as:

- business intent
- requirements
- local execution
- result review
- interpretation
- correction
- portfolio decisions

AI assistance included areas such as:

- implementation generation
- SQL
- Python
- debugging
- testing
- validation
- documentation
- alternative exploration

---

## AI-Assisted Implementation

Technical implementation created or substantially accelerated with AI assistance.

It does not imply autonomous acceptance of generated output.

---

## Local Verification

Executing implementation in the actual local environment and inspecting its behavior.

This is a key part of the project's AI-assisted workflow.

---

## Iterative Validation

The repeated process:

```text
Implement
   ↓
Run
   ↓
Observe
   ↓
Review
   ↓
Correct
   ↓
Run Again
```

---

# 19. Portfolio Concepts

## Core Documentation

The primary technical and business story of the project.

It includes:

```text
Business & Data Model
Data Platform
Analytics
Dashboard & Storytelling
Reliability & Validation
```

---

## Deep Dive

Documentation intended for readers who want more detail about:

```text
Engineering Decisions
Build Journey
Reproducibility
AI-Assisted Development
Limitations & Future Roadmap
```

---

## Reference Documentation

Structured technical reference material.

It includes:

```text
Glossary
Schema Reference
Metric Reference
Data Lineage
```

---

## Evidence Layer

Curated outputs used to support important repository claims.

The goal is evidence, not archival completeness.

---

## Portfolio Release

A curated version of the project intended for public technical review.

It is different from the complete historical development archive.

---

# 20. Key Distinctions Summary

Several distinctions appear repeatedly throughout the project.

```text
Account
≠
SaaS User
≠
Website Member
≠
Visitor
```

```text
Event
≠
State
```

```text
Current State
≠
Historical State
```

```text
Validation
≠
Data Quality
```

```text
Software Tests
≠
Data Quality Rules
≠
Serving Checks
```

```text
Duplicate Delivery
≠
Conflicting Duplicate
```

```text
Batch Identity
≠
Run Identity
```

```text
Analytical Grain
≠
Serving Grain
```

```text
Eligible
≠
Enabled
≠
Used
```

```text
Transition Count
≠
Distinct Account Count
```

```text
Historical Successful Run
≠
Clean-Machine Reproduction
```

```text
Result Reproduction
≠
Exact Synthetic Data Regeneration
```

These distinctions are important because many of the project's engineering and analytical decisions depend on them.

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
- [AI-Assisted Development](../deep-dive/ai_assisted_development.md)

### Reference

- [Schema Reference](schema_reference.md)
- [Metric Reference](metric_reference.md)
- [Data Lineage](data_lineage.md)

---

## Current Documentation Status

This glossary defines the current core terminology used throughout the repository.

The canonical pipeline, operational schema, dashboard-serving SQL and Power BI Project source are present in the repository. Additional terminology may be added as the remaining release artifacts and detailed mappings are finalized.
