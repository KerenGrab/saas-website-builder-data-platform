# Limitations & Future Roadmap

This document describes the current boundaries of the project and the directions in which it may be extended.

The purpose is to distinguish clearly between:

```text
Implemented
     ↓
Implemented but still being packaged / verified
     ↓
Planned Future Work
```

A portfolio project is more credible when its current scope and limitations are explicit.

---

## 1. Current Project Scope

The current project focuses on an end-to-end:

```text
Data Engineering
        +
Analytics
        +
Business Intelligence
```

workflow for a fictional Website Builder SaaS environment.

The implemented project includes work across:

- business and domain modeling
- synthetic source-data design
- relational data modeling
- PostgreSQL
- Python batch pipeline development
- input validation
- dependency-aware loading
- transactional loading
- duplicate handling
- rerun behavior
- run history
- Data Quality
- software testing
- analytical modeling
- SQL analytics
- serving views
- Power BI
- validation and evidence

The first public portfolio release is intended to focus on this existing scope.

---

## 2. Synthetic Business Environment

The project models a fictional SaaS company.

Therefore:

```text
The Business Model
        ↓
is realistic but fictional

The Data
        ↓
is synthetic

The Analytical Results
        ↓
describe the synthetic environment
```

The results should not be interpreted as real customer or commercial behavior.

The value of the project lies in the methodology:

- modeling
- engineering
- analytics
- validation
- interpretation

rather than in claims about a real company.

---

## 3. Local Architecture

The current implementation is primarily local.

The main technical environment is:

```text
Python
   ↓
Local Batch Pipeline
   ↓
PostgreSQL
   ↓
SQL / Serving
   ↓
Power BI
```

This means the project currently does not demonstrate a deployed cloud data platform.

It does not currently depend on services such as:

- AWS
- Azure
- GCP
- managed orchestration
- distributed compute
- cloud data warehouses

This is a deliberate scope boundary rather than an attempt to simulate technologies that were not required for the project.

---

## 4. Batch Rather Than Streaming

The pipeline is batch-oriented.

The current architecture is designed around a controlled source package and explicit batch semantics.

It does not currently implement:

```text
Real-Time Streaming
Event Broker Infrastructure
Continuous Processing
Change Data Capture
```

Technologies such as Kafka or similar streaming systems may be interesting future extensions, but they are not part of the current implementation.

---

## 5. Portfolio Scale vs Production Scale

The system demonstrates production-inspired engineering ideas, but it is not presented as a production SaaS data platform.

The current project does not demonstrate areas such as:

- horizontal scaling
- distributed execution
- multi-region infrastructure
- high-availability database architecture
- enterprise orchestration
- production secrets management
- centralized monitoring infrastructure
- formal incident response
- production SLAs

The architecture should therefore be interpreted according to its portfolio and learning scope.

---

## 6. No Live Operational Sources

The project does not currently ingest from real operational systems.

Instead, it uses a synthetic source package representing areas such as:

```text
Core Product
Event Tracking
Billing & Payment
Support
```

This means the project does not currently demonstrate source connectivity to systems such as:

- production APIs
- payment providers
- CRM systems
- support platforms
- message queues
- application databases

The synthetic layer exists to reproduce the data-engineering problems that such systems might create without relying on private external data.

---

## 7. Frozen Reference Dataset

The first release is intended to use a frozen synthetic reference dataset.

This provides a stable baseline for:

- pipeline validation
- reconciliation
- analytics
- reference results
- reproducibility

However, the frozen package should not be confused with a continuously evolving production data source.

The pipeline is currently optimized around the project's documented batch contract.

---

## 8. Synthetic Data Regeneration Is a Separate Concern

The project distinguishes between:

```text
Reproduce Results From Frozen Data
```

and:

```text
Regenerate the Exact Same Synthetic Dataset
```

The first is the primary reproducibility target for the initial public release.

The second should only be claimed if the full generation process is separately verified.

This distinction is documented in:

[Reproducibility](reproducibility.md)

---

## 9. Canonical Artifact Status

The repository contains selected canonical implementation artifacts:

- Python pipeline and CLI entry point
- software test suite
- operational schema and pipeline metadata SQL
- Data Quality SQL
- dashboard-serving SQL
- Power BI Project source
- three dashboard exports
- curated validation evidence

Standalone analytical SQL is not yet published under sql/30_analytics.
The full frozen dataset is distributed separately through the published data-v1.0 GitHub Release.

Remaining work must distinguish existing implementation from incomplete
packaging and artifacts that have not yet been independently verified.

---

## 10. Reproduction Status

The project has documented end-to-end reproduction against a clean
database, including reconciliation, Data Quality and regression evidence.

This is not equivalent to reproducing the full published system from
a fresh repository clone on another environment.

Fresh-clone verification remains a release gate.

---

## 11. Dependency Status

The repository contains populated dependency manifests.

The runtime requirements pin psycopg[binary]==3.3.5.
The development requirements add pytest==9.1.1.

Clean-environment installation and compatibility still require
release verification.

---

## 12. Database and SQL Packaging

The repository includes the operational schema, pipeline metadata,
dashboard-serving definitions and Data Quality SQL.

The setup and standalone analytics directories do not yet contain
complete published SQL implementations.

The final release guide must document database creation, SQL
application and pipeline execution order without depending on
undocumented local state.

---

## 13. Power BI Publication Status

The repository contains a Power BI Project source with a Report and
Semantic Model, as well as clean exports of all three dashboard pages.

Local Power BI state is excluded from Git.

Final verification must confirm that the project opens, resolves its
data-source configuration and renders without unpublished local cache.

---

## 14. Current Dashboard Scope

The dashboard currently focuses on three analytical stories:

```text
Customer Lifecycle & Multi-Dimensional Health

Website Audience Activity,
Engagement & Feedback

SaaS Product & Strategy Signals
```

It is designed primarily for analytical storytelling and decision support.

It is not currently a full enterprise reporting platform with:

- row-level security
- production deployment pipelines
- organizational workspace governance
- scheduled cloud refresh
- enterprise semantic-model governance

Those capabilities are outside the current project scope.

---

## 15. Analytical Results Depend on Metric Contracts

The project contains many numerical analytical results.

However, a number should not be interpreted independently from:

- population
- grain
- denominator
- time definition
- observation window
- historical state
- exclusions

The repository contains a Metric Reference, Data Lineage documentation and curated analytical evidence. Final review should ensure that published headline results have precise links to their definitions and supporting artifacts.

The project intentionally avoids presenting every historical number as a standalone claim.

---

## 16. Evidence Is Being Curated

The development history contains significant evidence:

- outputs
- screenshots
- logs
- SQL results
- test execution
- validation results

Publishing all of it would make the repository difficult to navigate.

The public `evidence/` layer therefore aims to contain only selected reference evidence.

The objective is:

```text
Enough Evidence to Verify Important Claims
```

rather than:

```text
Every Artifact Ever Produced
```

---

## 17. Security Cleanup Is Required Before Public Release

Historical development folders may contain local or sensitive configuration.

Examples include:

- IDE metadata
- database passwords
- environment files
- local paths
- temporary application state

These must remain outside the public repository.

The release process therefore includes:

```text
Canonical Artifact Selection
        ↓
Security Review
        ↓
Public Release
```

The repository `.gitignore` already excludes many local artifacts, but publication still requires manual review.

---

## 18. Historical Project Files Are Not Automatically Public Artifacts

An artifact may have been important during development without being appropriate for the public repository.

Examples include:

- raw chat transcripts
- temporary debugging scripts
- obsolete diagrams
- intermediate SQL
- IDE screenshots
- experimental files
- duplicated versions
- local logs

The public project is intentionally curated.

---

## 19. Documentation and Implementation Packaging

The repository contains substantial implementation alongside its
documentation.

The core documentation, canonical pipeline, test suite, operational SQL,
serving SQL, Data Quality SQL, Power BI source and selected evidence
are already present.

Remaining packaging gaps include standalone analytical SQL, integration
of the published data release into the setup guide, final setup
instructions and fresh-clone verification.

The repository remains a curated portfolio rather than an archive
of every historical development artifact.

---

# Future Roadmap

## 20. Roadmap Philosophy

Future work should extend the current project rather than replace it.

The existing system provides:

```text
Business Model
        ↓
Operational Data
        ↓
Data Platform
        ↓
Analytics
        ↓
BI
```

Future extensions can build on these foundations.

---

## 21. Phase 1 - Complete the Public v1.0 Release

The immediate priority is finishing release verification and packaging,
not adding new technologies.

Remaining work includes documentation review, integration of the
published dataset, analytical SQL scoping, security checks,
fresh-clone reproduction and versioned portfolio publication.

---

## 22. Canonical Pipeline Publication

The canonical Python pipeline and test suite are present in the repository.

Their documented setup and execution still need to be verified from
a fresh clone. Another historical implementation does not need to be
selected.

---

## 23. SQL Publication

The repository contains operational schema SQL, pipeline metadata,
dashboard-serving definitions and Data Quality SQL.

Standalone analytical SQL is not yet published under sql/30_analytics.

The release should either publish the intended analytical queries
or document that boundary explicitly.

The SQL setup order must be reproducible from published instructions.

---

## 24. Diagram Publication

A current entity-relationship diagram is available in the repository.

Additional platform, analytical and lineage diagrams remain optional
documentation improvements.

Only diagrams that accurately reflect the implementation should be
published as canonical.

---

## 25. Dashboard Gallery

Clean exports of all three dashboard pages are available under
assets/dashboard/.

Remaining presentation work includes verifying gallery links,
explanations and any selected README preview.

---

## 26. Evidence and Claim Mapping

The repository contains curated pipeline, schema, analytics, serving
and release-validation evidence.

Final review should confirm that prominent claims point to the correct
metric contracts, implementation and evidence.

Historical validation must not be presented as proof of an unperformed
fresh-clone test.

---

## 27. Improve Reproduction Automation

After manual clean-machine reproduction is verified, the process may be automated further.

Possible improvements include:

- database setup scripts
- one-command environment preparation
- scripted dataset verification
- automated schema application
- automated reference-result comparison

The objective would be to reduce manual setup while preserving transparency.

---

## 28. Continuous Integration

A future engineering extension could introduce CI.

For example:

```text
Push / Pull Request
        ↓
Install Dependencies
        ↓
Run Tests
        ↓
Static Validation
        ↓
Selected Data Checks
```

This could provide automatic feedback when the codebase changes.

CI should be added only after the canonical test and dependency environment are stable.

---

## 29. Containerization

Docker could be introduced as a later reproducibility improvement.

A future setup might include:

```text
Python Pipeline
        +
PostgreSQL
        ↓
Docker Compose
```

Potential benefits include:

- easier environment setup
- more consistent dependency versions
- reduced local configuration differences

Containerization is not required for the first release if the native reproduction workflow is already clear and verified.

---

## 30. Orchestration

A future version could move the batch pipeline into an orchestration framework.

Possible areas of exploration include:

- scheduled workflows
- task dependencies
- retries
- task-level observability
- parameterized runs

This would allow comparison between the current custom pipeline control flow and a dedicated orchestration system.

It is not part of the current implementation.

---

## 31. Cloud Deployment

A future extension could migrate parts of the project into a cloud architecture.

For example:

```text
Object Storage
      ↓
Orchestrated Pipeline
      ↓
Managed Database / Warehouse
      ↓
BI
```

The specific provider should be selected according to the learning goal rather than added merely for technology branding.

---

## 32. Data Warehouse Extension

The current project already contains dimensional modeling concepts.

A future version could expand this into a more explicit warehouse architecture.

Possible areas include:

- staging layer
- dimensional warehouse
- incremental loading
- slowly changing dimensions
- warehouse-specific transformations
- dedicated analytical storage

This would extend the current analytical model rather than discard it.

---

## 33. Incremental Processing

The current project is built around a frozen reference package and batch semantics.

A future extension could explore:

```text
New Data Since Previous Run
        ↓
Incremental Load
        ↓
Changed Historical State
        ↓
Updated Analytics
```

This would introduce additional concerns such as:

- watermarks
- late-arriving data
- incremental reconciliation
- update detection
- historical corrections

---

## 34. Streaming Extension

A more advanced future project version could introduce streaming events.

For example:

```text
Website / Product Event
        ↓
Event Broker
        ↓
Streaming Consumer
        ↓
Operational / Analytical Sink
```

This could be used to explore the difference between:

```text
Batch Event Processing
```

and:

```text
Near-Real-Time Event Processing
```

Streaming is not part of the current project.

---

# Machine Learning Roadmap

## 35. ML as a Future Extension

Machine Learning is intentionally excluded from the first public release.

The current project should first stand on its own as:

```text
Data Engineering
+
Analytics
+
Power BI
```

ML can later be added as a downstream consumer of the existing data platform.

This preserves a clear project story.

---

## 36. Why ML Should Come Later

The current project already provides many of the components needed before machine learning:

- defined business entities
- historical data
- validated source pipeline
- PostgreSQL data
- analytical grains
- metric contracts
- feature-related behavior
- customer lifecycle information
- website outcomes

Therefore, ML can be treated as:

```text
Extension of Existing Data Platform
```

rather than:

```text
Separate Unrelated Notebook
```

---

## 37. Potential ML Questions

Future ML work should begin with a business question rather than with an algorithm.

Possible directions include:

```text
Churn Risk

Conversion Propensity

Customer Engagement Risk

Feature Adoption Prediction

Website Outcome Prediction
```

The final choice should depend on:

- available labels
- observation windows
- leakage risk
- class balance
- business usefulness

---

## 38. ML Data Grain

Any future model would need an explicit prediction grain.

For example:

```text
Account × Observation Date
```

or:

```text
Website × Month
```

The prediction target should be defined relative to that grain.

For example:

```text
Features:
behavior through month M

Target:
churn in a future period
```

This would extend the same analytical discipline already used in the project.

---

## 39. Leakage Prevention

Historical modeling will be particularly important for ML.

A future model must avoid using information that would not have been known at prediction time.

The intended principle is:

```text
Features
→ only information available before prediction point

Target
→ future outcome
```

The existing time-aware data model provides a useful foundation for this work.

---

## 40. Train / Validation / Test Strategy

A future ML extension should define:

```text
Training Data
Validation Data
Test Data
```

according to the nature of the prediction problem.

For time-dependent customer behavior, random splitting may not always be appropriate.

Possible future evaluation should consider:

- temporal splits
- observation windows
- label windows
- leakage
- customer dependence

---

## 41. ML Should Connect Back to Business Value

A machine-learning extension should not exist only to demonstrate a model.

The flow should remain:

```text
Business Problem
        ↓
Prediction Question
        ↓
Prediction Grain
        ↓
Features
        ↓
Target
        ↓
Model
        ↓
Evaluation
        ↓
Business Interpretation
```

This would preserve the same business-first approach used throughout the current project.

---

## 42. Possible ML Integration With the Dashboard

If a future model becomes sufficiently validated, its outputs could later become another analytical signal.

For example:

```text
Historical Data
      ↓
ML Model
      ↓
Risk / Propensity Score
      ↓
Serving Layer
      ↓
Power BI
```

The dashboard could then combine:

```text
Descriptive Analytics
+
Predictive Signals
```

This is a future direction, not part of the current implementation.

---

## 43. Maintain Version Separation

When ML is added, the current project should remain understandable as a complete v1.

A possible evolution is:

```text
v1
Data Engineering + Analytics + BI

v2
Data Engineering + Analytics + BI + ML
```

This allows readers to distinguish the stable original project from later extensions.

---

# Roadmap Summary

## 44. Near-Term

The immediate release sequence is:

1. Finish the remaining Deep Dive, Reference and internal README review.
2. Complete repository-wide link and security checks.
3. Resolve the standalone analytical SQL publication boundary.
4. Use the published data-v1.0 release and checksum in the fresh-clone workflow.
5. Verify setup, dependencies and execution from a fresh clone.
6. Validate the Power BI source in the release environment.
7. Complete release evidence, versioning and v1.0 publication.

The existing pipeline, tests, core documentation and primary SQL
artifacts do not need to be selected again.

---

## 45. Medium-Term

Possible improvements include:

```text
CI
Containerization
Improved Setup Automation
Incremental Loading
Warehouse Expansion
```

These should be prioritized according to learning and portfolio value.

---

## 46. Longer-Term

Possible larger extensions include:

```text
Cloud Architecture
Orchestration
Streaming
Machine Learning
```

These should build on the existing project rather than obscure the current end-to-end story.

---

## 47. Guiding Principle

The project roadmap follows one main principle:

> Add technology when it solves a meaningful problem or creates a useful learning extension — not simply to increase the number of tools listed in the repository.

The current system already has a complete conceptual path:

```text
Business
   ↓
Data
   ↓
Engineering
   ↓
Analytics
   ↓
Business Intelligence
```

Future work should strengthen or extend that path.

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
- [Build Journey](build_journey.md)
- [Reproducibility](reproducibility.md)
- [AI-Assisted Development](ai_assisted_development.md)

### Reference

- [Data Lineage](../reference/data_lineage.md)
- [Schema Reference](../reference/schema_reference.md)
- [Metric Reference](../reference/metric_reference.md)

---

## Current Documentation Status

This document describes the current project boundaries and potential future development directions.

Future roadmap items are intentionally presented as planned extensions rather than as functionality already implemented.
