# Engineering Decisions

This document records selected engineering, data-modeling and analytical decisions made during the project.

The purpose is not to document every implementation detail.

Instead, it highlights decisions where multiple approaches were possible and where the chosen design affects correctness, reliability or analytical meaning.

A typical decision follows this structure:

```text
Problem
   ↓
Alternatives
   ↓
Decision
   ↓
Reasoning
   ↓
Trade-Off
   ↓
Impact
```

These decisions evolved throughout the project as business, technical and analytical requirements became clearer.

---

## 1. Separate Business Identities

### Problem

The system contains several kinds of people and organizations that could easily be modeled as one generic `User`.

Examples include:

- SaaS customers
- people operating the Website Builder
- registered Website members
- anonymous Website visitors

Combining them would simplify the schema initially but create ambiguity later.

### Decision

Keep the following concepts separate:

```text
Account
≠
SaaS User
≠
Website Member
≠
Visitor
```

### Reasoning

Each concept represents a different business role.

An Account is the SaaS customer entity.

A SaaS User operates the product on behalf of that Account.

A Website Member belongs to the audience side of a customer Website.

A Visitor represents website activity and may not be registered.

### Impact

This separation protects analytical populations.

For example:

```text
Customer Retention
→ Account population

Product Usage
→ SaaS customer side

Website Engagement
→ Visitor / Member population
```

The same identifier concept is therefore not reused for unrelated business roles.

### Trade-Off

The model becomes more detailed and requires more relationships.

The benefit is clearer business meaning and safer analytics.

---

## 2. Separate Events from States

### Problem

Some business facts describe something that happened at a specific time.

Others describe something that remained true for a period.

Representing both in the same way can make historical analysis difficult.

### Decision

Model events and states separately.

```text
EVENT

---------●--------------------→ time


STATE / PERIOD

---------|================|---→ time
      valid_from       valid_to
```

Examples of events include:

- payment completed
- page viewed
- feature used
- subscription transition

Examples of states include:

- Website is live
- Account is on a specific Plan
- Feature is available
- Subscription is active

### Reasoning

Historical questions often require knowing the state that existed when an event occurred.

### Impact

The analytical layer can ask questions such as:

> Which Plan was active when this Feature activity occurred?

rather than incorrectly using only the current Plan.

### Trade-Off

Historical periods require more complex joins and validation.

The benefit is historical correctness.

---

## 3. Use Half-Open Historical Periods

### Problem

Adjacent historical periods can become ambiguous if both periods include the same boundary timestamp.

For example:

```text
Period A ends on date X
Period B begins on date X
```

If both ends are inclusive, the same point can belong to two states.

### Decision

Use the conceptual interval:

```text
[valid_from, valid_to)
```

meaning:

```text
valid_from is included
valid_to is excluded
```

### Reasoning

This allows consecutive periods to meet cleanly:

```text
Period A
[Jan 1, Mar 1)

Period B
[Mar 1, Jun 1)
```

March 1 belongs only to Period B.

### Impact

Historical joins become less ambiguous.

### Trade-Off

The convention must be documented and used consistently across SQL and validation.

---

## 4. Validate Before Loading

### Problem

A pipeline could begin modifying the database and only discover invalid source data later.

This may require cleanup or create partial state.

### Alternatives

```text
Option A
Load first → validate later

Option B
Validate first → load only if valid
```

### Decision

Use:

```text
Validate
   ↓
Valid?
 ┌─┴─┐
Yes  No
 ↓    ↓
Load STOP
```

### Reasoning

Known-invalid input should be rejected before business tables are modified.

### Impact

Validation failures are easier to isolate from loading failures.

### Trade-Off

The pipeline performs additional work before loading and requires explicit source contracts.

---

## 5. Separate Validation from Data Quality

### Problem

The word "validation" can refer to very different checks.

A file may be structurally valid while producing an impossible business state after loading.

### Decision

Separate:

```text
Pre-Load Validation
        ↓
Can the input enter?

Post-Load Data Quality
        ↓
Does the resulting database state make sense?
```

### Reasoning

These layers detect different failure classes.

### Impact

A failure can be associated with the correct responsibility:

- source problem
- relationship problem
- implementation problem
- business-state problem

### Trade-Off

The project has more validation components to maintain.

The benefit is clearer diagnostics and stronger reliability.

---

## 6. Use Dependency-Aware Loading

### Problem

The relational model contains foreign-key dependencies.

Loading tables alphabetically or by filename can attempt to insert child records before their parents exist.

### Decision

Load according to dependency order.

```text
Parent
   ↓
Child
   ↓
Dependent Child
```

### Reasoning

Load order should be determined by the relational model, not by file naming.

### Impact

Foreign-key relationships can remain enforced during loading.

### Trade-Off

The pipeline needs explicit dependency metadata and load-planning logic.

---

## 7. Treat the Batch as an Atomic Business Load

### Problem

A multi-table load may fail after several tables have already been written.

Without transactional protection:

```text
Table A → loaded
Table B → loaded
Table C → failed
```

could leave inconsistent business state.

### Decision

Use one transactional boundary for the business load.

```text
BEGIN
  ↓
Load related data
  ↓
Success?
 ┌─┴────────┐
Yes         No
 ↓           ↓
COMMIT    ROLLBACK
```

### Reasoning

Related data should become visible as one consistent state.

### Impact

Failure does not intentionally leave partially loaded business data.

### Trade-Off

Large transactions may hold resources longer than smaller independent commits.

For the scale and purpose of this local portfolio project, consistency was prioritized.

---

## 8. Distinguish Duplicate Delivery from Conflict

### Problem

Event-based systems may deliver the same event more than once.

However, not every repeated identifier represents the same situation.

### Decision

Use payload comparison.

```text
same event_id
+
same payload
        ↓
Identical Duplicate
        ↓
Safe Skip
```

versus:

```text
same event_id
+
different payload
        ↓
Conflict
        ↓
STOP
```

### Reasoning

An identical redelivery is an operational duplicate.

A different payload under the same event identity indicates contradictory information.

Silently choosing one would hide a data-integrity problem.

### Impact

The pipeline can be tolerant of legitimate redelivery without accepting conflicting business data.

### Trade-Off

Deduplication requires enough information to determine payload equality.

---

## 9. Make Rerun Behavior Explicit

### Problem

Pipelines are rerun during:

- recovery
- debugging
- verification
- repeated execution

Without defined behavior, a rerun may duplicate data or silently process modified input.

### Decision

Use batch identity together with an input fingerprint.

```text
same batch_id
+
same fingerprint
        ↓
SKIP
```

```text
same batch_id
+
different fingerprint
        ↓
STOP
```

### Reasoning

The same logical batch with identical content is already known.

The same logical batch identity with changed content is suspicious and requires explicit handling.

### Impact

Rerun behavior is predictable.

### Trade-Off

This policy is intentionally strict and is designed around the project's batch contract rather than every possible production ingestion model.

---

## 10. Separate Batch Identity from Run Identity

### Problem

A logical batch and an execution attempt are not the same thing.

The same batch may have:

- a failed attempt
- another execution
- a skipped rerun

### Decision

Model them separately.

```text
Batch
  │
  ├── Run 1
  ├── Run 2
  └── Run 3
```

### Reasoning

Batch identity answers:

> What source unit is this?

Run identity answers:

> Which execution attempt is this?

### Impact

Execution history becomes easier to interpret and audit.

### Trade-Off

Operational metadata becomes slightly more complex.

---

## 11. Enforce Integrity in Both Python and PostgreSQL

### Problem

Relying only on application logic means database integrity depends entirely on Python behaving correctly.

Relying only on database constraints means many input problems are discovered late.

### Decision

Use both.

```text
Python
→ early validation

PostgreSQL
→ persisted integrity
```

### Reasoning

The two layers protect different boundaries.

### Impact

Problems can be rejected early while the database still protects itself from invalid persisted state.

### Trade-Off

Some rules appear conceptually in more than one layer and must remain consistent.

---

## 12. Define Analytical Grain Before Writing SQL

### Problem

SQL can produce technically valid results at the wrong grain.

For example:

```text
Account × Month
```

is different from:

```text
Website × Month
```

because one Account may own multiple Websites.

### Decision

Every important analysis begins with an explicit grain.

Representative grains include:

```text
Account × Journey
Account × Month
Account × Feature × Month
Website × Month
Website × Feature × Month
Account × Churn Occurrence
```

### Reasoning

Grain determines what one row means.

Without that definition, joins and aggregations can silently double-count data.

### Impact

Metric definitions and SQL can be reviewed against a clear analytical unit.

### Trade-Off

Analytical design requires more work before implementation begins.

---

## 13. Treat the Denominator as a Business Decision

### Problem

A percentage can look correct while using the wrong population.

Feature Adoption is a clear example.

### Weak Definition

```text
Accounts Using Feature
----------------------
All Accounts
```

### Decision

Where appropriate, use eligibility-aware populations.

```text
Accounts That Adopted
---------------------
Accounts Eligible to Adopt
```

### Reasoning

Accounts without access to a Feature did not have the same opportunity to adopt it.

### Impact

The resulting metric has clearer business meaning.

### Trade-Off

Eligibility requires historical Plan and entitlement logic, making implementation more complex.

---

## 14. Use Historical State for Historical Analytics

### Problem

Using the current Plan for an event that happened months earlier can produce incorrect eligibility and segmentation.

### Decision

Resolve state as of the analytical event or observation time.

```text
Historical Event
      ↓
Relevant Date
      ↓
Plan Active Then
      ↓
Eligibility Then
```

### Reasoning

Historical questions require historical context.

### Impact

Feature Adoption, commercial analysis and other metrics can reflect the state that actually existed.

### Trade-Off

Historical joins are more complex than current-state joins.

---

## 15. Preserve Time Definitions Instead of Forcing One Interpretation

### Problem

Metrics such as retention can be measured under different legitimate time definitions.

For example:

```text
Month-End Retention
```

and:

```text
Exact-Anniversary Retention
```

do not necessarily produce the same result.

### Decision

Document the time contract instead of silently treating one definition as universally correct.

### Reasoning

Different definitions may answer slightly different business questions.

### Impact

Results are interpreted according to their stated contract.

### Trade-Off

Documentation becomes more important because similar metric names may hide different time semantics.

---

## 16. Separate Analytical Grain from Serving Grain

### Problem

The dashboard may need a more aggregated representation than the underlying analytical model.

For example:

```text
Website × Month
```

may feed:

```text
Month-Level Dashboard Output
```

### Decision

Allow analytical and serving grains to differ when the transformation is explicit.

### Reasoning

A serving layer exists to provide downstream consumers with a controlled interface.

It does not need to expose every lower-level row.

### Impact

Power BI receives data shaped for its intended use while the lower-level analytical grain remains documented.

### Trade-Off

The serving layer requires its own grain and validation rules.

---

## 17. Use a Serving Layer Before Power BI

### Problem

Connecting Power BI directly to many operational tables would move substantial business logic into the visualization layer.

That can create:

- duplicated logic
- inconsistent denominators
- unclear grain
- difficult validation

### Decision

Use:

```text
Operational Data
      ↓
Analytical Logic
      ↓
Serving Views
      ↓
Power BI
```

### Reasoning

The analytical meaning should be established before visualization.

### Impact

Dashboard inputs are easier to validate and explain.

### Trade-Off

The project contains another explicit layer to maintain.

---

## 18. Isolate Dashboard Filters When Necessary

### Problem

A Power BI slicer may affect visuals that should preserve a different population or context.

### Decision

Control filter interactions rather than assuming every filter should affect every visual.

### Reasoning

Visual interaction can change analytical meaning.

For example, a Feature selector may reasonably affect Feature Adoption visuals but should not automatically redefine unrelated customer lifecycle metrics.

### Impact

Dashboard behavior remains closer to the intended metric contracts.

### Trade-Off

The report requires more deliberate configuration and validation.

---

## 19. Keep Conceptual and Physical Models Distinct

### Problem

Early conceptual diagrams were designed to understand the business domain.

Later logical and physical models contain much more implementation detail.

Treating an early conceptual ERD as the final database schema would misrepresent the project.

### Decision

Document the stages separately.

```text
Conceptual Model
      ↓
Logical Relational Model
      ↓
Physical PostgreSQL Implementation
```

### Reasoning

Each model answers a different question.

### Impact

Portfolio readers can understand both the business thinking and the technical implementation without confusing them.

### Trade-Off

Multiple diagrams and documents may be needed.

---

## 20. Publish a Frozen Reference Dataset Separately from Git

### Problem

The complete synthetic source package contains large files and should not be committed directly into normal Git history.

### Decision

Use the repository for:

```text
Contracts
+
Curated Samples
+
Generator Source
```

and publish the verified full frozen input package separately as a release artifact.

### Reasoning

This keeps Git history manageable while preserving reproducibility.

### Impact

The repository can remain lightweight while a specific dataset version can still be referenced.

### Trade-Off

A complete reproduction requires downloading the release dataset separately.

---

## 21. Keep Full Data Regeneration Separate from Result Reproduction

### Problem

Two different claims can easily be confused:

```text
Can I reproduce the analytical results
from the frozen input?

vs

Can I regenerate the exact same
synthetic source package from scratch?
```

### Decision

Treat these as separate reproducibility goals.

### Reasoning

A verified frozen dataset can support result reproduction even if the complete synthetic generation chain has not yet been proven to reproduce every source file byte-for-byte.

### Impact

Public claims can remain precise.

### Trade-Off

The documentation must clearly distinguish the two workflows.

---

## 22. Use Human-Directed, AI-Assisted Development Transparently

### Problem

AI contributed significantly to implementation.

Presenting the project as entirely manually coded would be inaccurate.

Presenting it as autonomously built by AI would also be inaccurate.

### Decision

Describe the workflow as:

> Human-Directed, AI-Assisted Engineering

### Human Direction Included

- business intent
- requirements
- deciding what questions matter
- reviewing alternatives
- local execution
- interpretation of outputs
- identifying problems
- requesting corrections
- validating results

### AI Assistance Included

- implementation suggestions
- Python generation
- SQL generation
- debugging
- test creation
- validation logic
- documentation
- implementation alternatives

### Workflow

```text
Requirement
      ↓
Discussion
      ↓
AI-Assisted Implementation
      ↓
Local Execution
      ↓
Observed Result
      ↓
Review
      ↓
Iteration
      ↓
Validated Result
```

### Reasoning

The goal is accurate disclosure rather than minimizing or exaggerating either role.

### Impact

The repository can show practical AI-assisted engineering as part of the development methodology.

### Trade-Off

Some implementation authorship cannot be meaningfully reduced to a simple percentage.

The project therefore avoids artificial claims such as "X% written by AI."

---

## 23. Treat AI-Generated Tests as Candidates, Not Proof

### Problem

A test generated by AI is not automatically evidence that a system is correct.

The test itself may contain incorrect assumptions.

### Decision

Evidence comes from the verification cycle:

```text
Requirement
      ↓
Test / Check
      ↓
Execution
      ↓
Observed Result
      ↓
Review
      ↓
Correction if Necessary
```

### Reasoning

The existence of code is not the same as validated behavior.

### Impact

The repository emphasizes executed evidence rather than generated artifacts alone.

### Trade-Off

Verification requires additional time and review.

---

## 24. Keep Reliability Counts Separate

### Problem

The project contains several different validation mechanisms.

Adding them together into a single number would create a misleading impression.

### Decision

Keep them separately identified as:

```text
Software Tests
Data Quality Rules
Serving Checks
Reconciliation
Database Constraints
Pre-Load Validation
```

### Reasoning

Each mechanism answers a different question.

### Impact

Reliability claims are more interpretable.

### Trade-Off

The headline numbers may look less dramatic, but they are more meaningful.

---

## 25. Prefer Claim → Evidence Documentation

### Problem

Portfolio projects often contain statements such as:

```text
"Reliable pipeline"
"Millions of rows"
"Extensive testing"
```

without showing how those claims were established.

### Decision

Where practical, connect important claims to evidence.

```text
Claim
   ↓
Implementation
   ↓
Reference Output
   ↓
Release Version
```

### Reasoning

A technical portfolio is stronger when important claims are inspectable.

### Impact

The repository includes a dedicated evidence layer.

### Trade-Off

Publication requires selecting and cleaning reference evidence rather than only publishing source code.

---

## 26. Design for Local Portfolio Scope Before Production Scale

### Problem

It would be easy to add technologies such as:

- cloud services
- orchestration platforms
- streaming systems
- containers
- distributed processing

only to make the architecture appear more advanced.

### Decision

Keep the current architecture aligned with the actual problem and implementation.

The current platform is intentionally:

```text
Local
Batch-Oriented
Python-Based
PostgreSQL-Based
Analytics-Focused
```

### Reasoning

Architecture should reflect project requirements rather than technology collection.

### Impact

The project emphasizes correctness and end-to-end reasoning within its actual scope.

### Trade-Off

Production infrastructure remains outside the current implementation.

It can be explored later as an extension.

---

## 27. Decision Summary

The major decisions in the project follow a common theme:

```text
Explicit Business Meaning
        ↓
Explicit Data Contracts
        ↓
Explicit Failure Behavior
        ↓
Explicit Analytical Definitions
        ↓
Explicit Validation
        ↓
Traceable Outputs
```

The project favors clarity and explainability over hidden assumptions.

---

## Related Documentation

### Core Story

- [Business & Data Model](../core/01_business_and_data_model.md)
- [Data Platform](../core/02_data_platform.md)
- [Analytics](../core/03_analytics.md)
- [Dashboard & Storytelling](../core/04_dashboard_and_storytelling.md)
- [Reliability & Validation](../core/05_reliability_and_validation.md)

### Deep Dive

- [Build Journey](build_journey.md)
- [Reproducibility](reproducibility.md)
- [AI-Assisted Development](ai_assisted_development.md)
- [Limitations & Future Roadmap](limitations_and_roadmap.md)

### Reference

- [Glossary](../reference/glossary.md)
- [Data Lineage](../reference/data_lineage.md)
- [Schema Reference](../reference/schema_reference.md)
- [Metric Reference](../reference/metric_reference.md)

---

## Current Documentation Status

These decisions describe the current project architecture and analytical methodology.

Additional implementation-specific trade-offs may be added as canonical Python, SQL, Power BI and data artifacts are selected and verified for the public release.