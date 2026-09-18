# Dashboard Serving Validation

This document records validation evidence for the canonical dashboard-serving layer of the SaaS Website Builder Data Platform.

The serving layer provides a controlled SQL interface between the operational / analytical logic and the Power BI reporting layer.

It allows the dashboard to consume purpose-built analytical outputs rather than querying the full operational schema directly.

---

## 1. Canonical Serving Artifact

The validated serving SQL artifact is:

```text
sql/40_serving/001_dashboard_views.sql
```

SHA256:

```text
0298CA6C67B90BE6C472AA5B593E6FD41782D14242236892F358CFA3164D543B
```

This hash identifies the exact version-controlled SQL artifact used for the inventory in this document.

[View Canonical Dashboard Serving SQL](../../../sql/40_serving/001_dashboard_views.sql)

---

## 2. Serving Architecture

The reporting path follows:

```text
Operational PostgreSQL Schema
            ↓
Analytical Logic
            ↓
Dashboard Serving Views
            ↓
Power BI Semantic Model
            ↓
Dashboard Pages
```

The serving layer therefore acts as a stable analytical interface.

Power BI does not need to reconstruct the full operational relational model independently.

---

## 3. Canonical View Inventory

Direct inspection of the canonical SQL identified:

```text
12 CREATE VIEW definitions
```

The views are:

```text
dashboard.vw_commercial_transition
dashboard.vw_conversion_horizon
dashboard.vw_feature
dashboard.vw_feature_adoption
dashboard.vw_lifecycle_kpis
dashboard.vw_locked_feature_signal
dashboard.vw_paid_retention_horizon
dashboard.vw_product_paid_aligned
dashboard.vw_rating_snapshot
dashboard.vw_support_monthly
dashboard.vw_support_summary
dashboard.vw_website_monthly
```

Verified count:

```text
12 / 12 serving views
```

---

## 4. View Responsibilities

| Serving View | Primary Analytical Role |
|---|---|
| `dashboard.vw_commercial_transition` | Commercial plan / subscription transition analysis |
| `dashboard.vw_conversion_horizon` | First-paid-conversion results across defined time horizons |
| `dashboard.vw_feature` | Feature reference data used by feature-oriented reporting |
| `dashboard.vw_feature_adoption` | Eligibility-aware feature adoption analysis |
| `dashboard.vw_lifecycle_kpis` | Customer lifecycle KPI serving layer |
| `dashboard.vw_locked_feature_signal` | Locked-feature attempt / access signal analysis |
| `dashboard.vw_paid_retention_horizon` | Paid-retention results across defined horizons |
| `dashboard.vw_product_paid_aligned` | Product-state versus paid-state comparison |
| `dashboard.vw_rating_snapshot` | Rating and feedback snapshot reporting |
| `dashboard.vw_support_monthly` | Monthly support activity analysis |
| `dashboard.vw_support_summary` | Aggregated support KPI summary |
| `dashboard.vw_website_monthly` | Website audience, activity and engagement reporting |

These views represent reporting interfaces rather than operational source tables.

---

## 5. Power BI Mapping

The Power BI semantic model consumes the serving layer through corresponding reporting tables.

The verified mapping is:

| Power BI Table | PostgreSQL Serving View |
|---|---|
| Commercial Transitions | `dashboard.vw_commercial_transition` |
| Conversion | `dashboard.vw_conversion_horizon` |
| Feature | `dashboard.vw_feature` |
| Feature Adoption | `dashboard.vw_feature_adoption` |
| Lifecycle KPIs | `dashboard.vw_lifecycle_kpis` |
| Locked Feature Signal | `dashboard.vw_locked_feature_signal` |
| Paid Retention | `dashboard.vw_paid_retention_horizon` |
| Product vs Paid | `dashboard.vw_product_paid_aligned` |
| Rating Snapshot | `dashboard.vw_rating_snapshot` |
| Support Monthly | `dashboard.vw_support_monthly` |
| Support Summary | `dashboard.vw_support_summary` |
| Website Monthly | `dashboard.vw_website_monthly` |

This provides a direct reporting contract:

```text
12 PostgreSQL Serving Views
            ↓
12 Power BI Semantic-Model Tables
```

---

## 6. Serving Domains

The 12 views can be understood through several analytical domains.

### Customer Lifecycle

```text
vw_lifecycle_kpis
vw_conversion_horizon
vw_paid_retention_horizon
vw_product_paid_aligned
```

These support customer-lifecycle reporting such as:

```text
Activation / Conversion
Paid Retention
Product vs Paid State
Lifecycle Health
```

---

### Feature Adoption

```text
vw_feature
vw_feature_adoption
vw_locked_feature_signal
```

These support analysis of:

```text
Feature Reference
Eligibility
Adoption
Locked-Access Signals
```

The separation is important because:

```text
Feature Exists
≠
Account Eligible
≠
Feature Enabled
≠
Feature Used
```

---

### Website Outcomes

```text
vw_website_monthly
vw_rating_snapshot
```

These support Website-level reporting such as:

```text
Sessions
Page Views
Engagement
Friction
Comments
Ratings
```

Website-level outputs remain distinct from Account-level customer metrics.

---

### Commercial and Support Signals

```text
vw_commercial_transition
vw_support_monthly
vw_support_summary
```

These provide reporting interfaces for:

```text
Commercial Transitions
Support Volume
Support Resolution
Operational Customer Signals
```

---

## 7. Reporting Boundary

The serving views intentionally separate reporting logic from the raw operational model.

Conceptually:

```text
Operational Tables
        ↓
Complex Historical / Analytical Logic
        ↓
Serving View
        ↓
Simple Reporting Interface
```

This provides several benefits:

```text
Consistent Metric Logic
Stable Reporting Grain
Reduced Power BI Complexity
Reusable Analytical Definitions
Clearer Data Contracts
```

The dashboard therefore consumes curated outputs instead of repeatedly rebuilding complex joins and historical logic inside the BI layer.

---

## 8. Analytical Grain Protection

Different reporting questions operate at different grains.

Examples include:

```text
Account × Journey
Account × Month
Account × Feature × Month
Website × Month
```

The serving layer helps preserve these distinctions before data reaches Power BI.

This reduces the risk of accidentally mixing:

```text
Account-level metrics
with
Website-level metrics
```

or interpreting one analytical population as another.

---

## 9. Historical Logic

Several dashboard questions depend on historical state rather than current state.

For example:

```text
Activity Date
      ↓
Historical Plan / Eligibility State
      ↓
Analytical Result
```

The serving layer exposes downstream results after the relevant historical logic has already been resolved.

This supports metrics such as:

```text
Paid Retention
Feature Eligibility
Product vs Paid State
Commercial Transitions
```

without requiring the visualization layer to reconstruct every historical relationship.

---

## 10. Dashboard Pages

The serving views feed a three-page Power BI dashboard.

### Customer Lifecycle & Multi-Dimensional Health

Primary analytical themes include:

```text
Conversion
Paid Retention
Product vs Paid State
Feature Adoption
Paid Churn / Lifecycle Signals
```

---

### Website Audience Activity, Engagement & Feedback

Primary analytical themes include:

```text
Sessions
Page Views
Forms
Friction
Pages per Session
Session Duration
Comments
Ratings
```

---

### SaaS Product & Strategy Signals

Primary analytical themes include:

```text
Feature Adoption
Locked Feature Signals
Support
Commercial Transitions
Product Strategy Signals
```

Dashboard implementation details and screenshots are documented in:

[Dashboard Documentation](../../../dashboard/README.md)

---

## 11. Why Views Instead of Direct Operational Queries

The operational schema is optimized for representing business entities, history, events, and integrity.

The dashboard has different requirements.

It needs:

```text
Stable Analytical Outputs
Defined Reporting Grains
Reusable Metric Logic
Simpler BI Queries
Consistent Business Meaning
```

Therefore:

```text
Operational Schema
≠
Dashboard Serving Interface
```

The serving layer provides an explicit architectural boundary between the two.

---

## 12. Version-Controlled BI Contract

Because the serving views are defined in version-controlled SQL, the reporting interface is reviewable alongside the rest of the platform.

The contract is represented by:

```text
sql/40_serving/001_dashboard_views.sql
```

rather than being hidden exclusively inside Power BI transformations.

This makes the analytical interface easier to:

```text
Inspect
Review
Recreate
Version
Test
Document
```

---

## 13. Relationship to the Power BI Project

The repository also contains the Power BI project files under:

```text
dashboard/powerbi/
```

The semantic model references the PostgreSQL serving views represented in this document.

The Power BI project and serving SQL therefore form two separate but connected artifacts:

```text
PostgreSQL Serving Layer
        ↓
Version-Controlled SQL Contract

Power BI Project
        ↓
Version-Controlled Reporting Contract
```

Together they make the reporting path inspectable without requiring the dashboard logic to exist only inside a binary `.pbix` file.

---

## 14. Validation Boundary

This document distinguishes between two forms of evidence.

### Static Serving Validation

Direct inspection of the canonical SQL verifies:

```text
Canonical SQL artifact
SHA256 identity
12 CREATE VIEW definitions
12-view inventory
```

### Broader Platform Validation

Separate end-to-end evidence verifies that the pipeline, PostgreSQL target state, data-quality framework and regression suite operate correctly together.

See:

[End-to-End Reproduction Evidence](../../release-validation/end_to_end_reproduction.md)

This document intentionally does not invent a separate serving-test count that has not been re-verified from a canonical artifact.

---

## 15. Related Evidence

Pipeline behavior:

[Pipeline Behavior Validation](../pipeline/pipeline_behavior_validation.md)

Operational schema:

[Operational Schema Validation](../schema/operational_schema_validation.md)

End-to-end reproduction:

[End-to-End Reproduction Evidence](../../release-validation/end_to_end_reproduction.md)

Dashboard documentation:

[Dashboard Documentation](../../../dashboard/README.md)

---

## Verification Summary

| Verification | Result |
|---|---:|
| Canonical serving SQL identified | VERIFIED |
| Serving SQL SHA256 captured | VERIFIED |
| `CREATE VIEW` definitions | 12 |
| Serving-view inventory extracted | 12 / 12 |
| Power BI serving mappings documented | 12 / 12 |
| Lifecycle serving layer | VERIFIED |
| Feature serving layer | VERIFIED |
| Website reporting layer | VERIFIED |
| Commercial / support serving layer | VERIFIED |
| Reporting architecture documented | VERIFIED |

---

## Final Result

```text
Canonical Serving SQL        VERIFIED
SQL Identity / SHA256        VERIFIED
Serving Views                12 / 12
Power BI Mappings            12 / 12
Lifecycle Interface          VERIFIED
Feature Interface            VERIFIED
Website Interface            VERIFIED
Commercial / Support Layer   VERIFIED
Reporting Boundary           DOCUMENTED
```

The canonical dashboard-serving layer provides a version-controlled SQL contract between the platform's operational / analytical logic and the Power BI semantic model.