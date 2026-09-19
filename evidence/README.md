# Evidence

This directory contains reproducible validation evidence for the SaaS Website Builder Data Platform.

The goal is to separate implementation claims from verifiable results. Each evidence document records a specific validation boundary and points back to the canonical version-controlled artifacts that produce or define the result.

> The project uses synthetic data. Reported analytical values describe the generated SaaS scenario and should not be interpreted as production business performance.

---

## Evidence Map

### End-to-End Reproduction

[`release-validation/end_to_end_reproduction.md`](release-validation/end_to_end_reproduction.md)

Validates the complete frozen-data pipeline run against the canonical input release.

Verified results include:

- 49 / 49 source datasets processed
- 44 CSV + 5 JSONL files
- 2,903,577 raw records scanned
- 3,638 exact duplicate deliveries skipped
- 2,899,939 target rows loaded
- 49 / 49 row-count checks passed
- 49 / 49 SHA256 checks passed
- transaction committed successfully
- 32 / 32 data-quality rules passed with 0 violations
- 39 / 39 final regression tests passed

This is the strongest end-to-end reproduction checkpoint for the frozen release.

---

## Reference Results

### Pipeline Behavior

[`reference-results/pipeline/pipeline_behavior_validation.md`](reference-results/pipeline/pipeline_behavior_validation.md)

Documents the dedicated pipeline-behavior validation checkpoint.

Coverage includes:

- validation-before-load behavior
- deterministic transformation and projection
- duplicate KEEP / SKIP / FAIL semantics
- dependency-aware load planning
- target safety and reconciliation
- transaction COMMIT / ROLLBACK behavior
- no partial writes on failure
- batch ID and fingerprint handling
- safe rerun behavior
- persistent run-state semantics

The historical Part 9F checkpoint contained 32 dedicated behavior tests. The later end-to-end regression suite grew to 39 tests; both checkpoints are preserved rather than conflated.

---

### Operational Schema

[`reference-results/schema/operational_schema_validation.md`](reference-results/schema/operational_schema_validation.md)

Validates the canonical PostgreSQL operational DDL.

Verified structural inventory:

- 49 tables
- 49 primary-key declarations
- 70 foreign-key reference declarations
- 11 UNIQUE constraints
- 47 CHECK constraints
- 4 PostgreSQL functions
- 6 triggers

This evidence also documents historical-period modeling, lifecycle/event integrity rules, and the boundary between the operational schema and downstream analytics.

---

### Dashboard Serving Layer

[`reference-results/serving/dashboard_serving_validation.md`](reference-results/serving/dashboard_serving_validation.md)

Validates the version-controlled PostgreSQL serving layer used by Power BI.

Verified inventory:

- 12 canonical dashboard views
- exact Power BI table-to-view mappings
- lifecycle, conversion, retention, feature, support, commercial-transition, rating, and website reporting domains
- explicit reporting grains and serving responsibilities

The document does not invent or restate a separate serving-test count that could not be re-verified from a canonical artifact.

---

### Analytics Results

[`reference-results/analytics/analytics_results_validation.md`](reference-results/analytics/analytics_results_validation.md)

Records analytical outputs re-queried directly from the canonical PostgreSQL serving layer.

Verified result families include:

- First Paid Conversion
- Paid Retention
- Product vs Paid Alignment
- Eligibility-Aware Feature Adoption
- Commercial Transitions
- Website Audience and Outcome Metrics
- Rating and Feedback Snapshot

Examples of verified outputs:

- D30 First Paid Conversion: 9.39%
- D180 First Paid Conversion: 17.35%
- M12 Paid Retention: 66.43%
- M12 Product/Paid Gross Mismatch: 21.68%
- Overall eligibility-aware Feature Adoption: 46.09%
- Commercial Transitions: 786
- Sessions: 240,000
- Page Views: 573,384
- Average Rating: 3.95

These results were queried directly from PostgreSQL rather than copied from historical notes or dashboard screenshots.

---

## Evidence Boundaries

The evidence in this directory intentionally distinguishes between different kinds of validation.

### Implementation Evidence

Shows that version-controlled code and database artifacts exist and have defined structure.

Examples:

- PostgreSQL DDL
- pipeline code
- serving-view SQL
- Power BI project files

### Behavioral Evidence

Shows that the system behaves correctly under expected and failure conditions.

Examples:

- rollback on failure
- rerun safety
- duplicate handling
- fingerprint conflict detection
- validation-before-load

### Data Evidence

Shows that the frozen release can be processed and reconciled correctly.

Examples:

- row counts
- SHA256 verification
- deduplication reconciliation
- DQ results

### Analytical Evidence

Shows that key portfolio metrics can be reproduced from the canonical database.

Examples:

- conversion
- retention
- feature adoption
- commercial transitions
- website outcomes

---

## Important Modeling Boundary

The analytical design documents describe:

- 7 analytical fact designs
- 5 conformed dimensions

This should not be interpreted as a claim that the repository currently contains seven physical analytical fact tables.

The reproducible PostgreSQL implementation exposes the verified analytical outputs through version-controlled serving views.

---

## Related Repository Areas

| Area | Location |
|---|---|
| Pipeline | [`../pipeline/`](../pipeline/) |
| Pipeline entry point | [`../run_pipeline.py`](../run_pipeline.py) |
| Tests | [`../tests/`](../tests/) |
| Operational schema | [`../sql/10_schema/`](../sql/10_schema/) |
| Pipeline metadata | [`../sql/20_operational_metadata/`](../sql/20_operational_metadata/) |
| Standalone analytical SQL (not yet published) | [`../sql/30_analytics/`](../sql/30_analytics/) |
| Dashboard serving SQL | [`../sql/40_serving/`](../sql/40_serving/) |
| Validation SQL | [`../sql/90_validation/`](../sql/90_validation/) |
| Power BI project | [`../dashboard/powerbi/`](../dashboard/powerbi/) |
| Project documentation | [`../docs/`](../docs/) |

---

## Current Validation Status

The canonical portfolio evidence currently demonstrates:

**Data release → validation → transformation → PostgreSQL load → data quality → serving views → analytical results → Power BI consumption**

with explicit reproducibility, integrity, testing, and validation boundaries.
