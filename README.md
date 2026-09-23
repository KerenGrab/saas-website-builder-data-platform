# SaaS Website Builder Data Platform

An end-to-end **Data Engineering & Analytics portfolio project** that models the data platform of a fictional Website Builder SaaS company.

The project follows the full path from business and domain modeling, through synthetic source data, PostgreSQL and a Python data pipeline, to analytical modeling, SQL, serving views and a Power BI dashboard.

A subsequent Machine Learning extension explores six-month paid retention using the existing data platform.

> **Project context:** This is a local portfolio project built with synthetic data.<br>
> Development was human-directed and strongly AI-assisted across design, implementation, debugging, testing and documentation.

---

## What This Project Demonstrates

The project was designed to connect five areas that are often presented separately:

- **Business & system thinking** — translating a SaaS business into entities, relationships, lifecycle states and historical rules.
- **Data engineering** — ingestion, validation, dependency-aware loading, transactions, duplicate handling, rerun semantics and run history.
- **Analytics** — defining populations, grains, denominators and time semantics before implementing metrics in SQL.
- **Validation & communication** — Data Quality checks, software tests, reconciliation, serving validation and Power BI storytelling.
- **Applied Machine Learning** - historical feature preparation, model training and holdout evaluation for paid retention.

---

## Business Context

The fictional product is a **Website Builder SaaS platform**.

The data model represents three connected perspectives:

1. The SaaS company operating the product.
2. Customers who create and manage websites.
3. Visitors and members who interact with those websites.

This separation is important throughout the project because concepts such as:

`Account` ≠ `SaaS User` ≠ `Website Member` ≠ `Visitor`

represent different actors and analytical populations.

[Explore the Business & Data Model](docs/core/01_business_and_data_model.md)

---

## End-to-End Data Platform

```text
Business & Domain Design
        ↓
Synthetic Data Sources
        ↓
Python Data Pipeline
        ↓
PostgreSQL
        ↓
Analytical Modeling & SQL
        ↓
Serving Layer
        ↓
Power BI
        ↓
Business Interpretation
```

The platform was designed around validation-before-load, historical correctness, transactional safety and explicit analytical definitions.

[Explore the Data Platform](docs/core/02_data_platform.md)

---

## Analytics

The analytical layer was built around realistic product and management questions rather than arbitrary metrics.

Representative analytical areas include:

- First Paid Conversion
- Paid Retention
- Product vs Paid Activity
- Eligibility-Aware Feature Adoption
- Website Outcomes
- Commercial Transitions

Each analysis is defined through:

```text
Business Question
        ↓
Population
        ↓
Grain
        ↓
Time Definition
        ↓
Metric Contract
        ↓
SQL
        ↓
Serving Output
        ↓
Business Interpretation
```

[Explore the Analytics](docs/core/03_analytics.md)

---

## Dashboard & Storytelling

The Power BI dashboard translates the analytical layer into decision-support information.

It contains three business-oriented pages:

- **Customer Lifecycle & Multi-Dimensional Health**
- **Website Audience Activity, Engagement & Feedback**
- **SaaS Product & Strategy Signals**

The dashboard was designed around realistic management and product questions, not around arbitrary metrics.

The dashboard represents the point where the technical work becomes business-facing information: modeled and validated data is translated into interpretable signals that can support product, operational and managerial decision-making.

[Explore Dashboard & Storytelling](docs/core/04_dashboard_and_storytelling.md)

---

## Machine Learning Extension - M6 Paid Retention

The project includes a reproducible Machine Learning proof of
concept built on the existing data platform.

The experiment investigates whether customer behavior observed
at the first Free-to-Paid conversion can help identify accounts
that may no longer be paid six months later.

It includes:

- SQL-based feature preparation and a labeled dataset of 316 accounts.
- A Logistic Regression model using three customer-behavior features.
- A separate holdout evaluation, with 7 actual Not Paid accounts among the 10 highest-risk accounts.

The experiment uses **synthetic data** and is a retrospective
proof of concept, not a production-ready prediction service.

[Explore the Machine Learning extension](ml/README.md)

---

## Reliability & Validation

Reliability is implemented as multiple validation layers rather than a single test stage.

```text
Source Data
    ↓
Input Validation
    ↓
Transformation & Integrity Checks
    ↓
Transactional Load
    ↓
Database Constraints
    ↓
Data Quality
    ↓
Reconciliation
    ↓
Analytical / Serving Validation
    ↓
Power BI
```

The project separately tracks:

- Data Quality rules
- Software tests
- Reconciliation checks
- Serving-layer validation

These are intentionally treated as different reliability mechanisms rather than combined into one generic test count.

[Explore Reliability & Validation](docs/core/05_reliability_and_validation.md)

---

## Technology Stack

### Data Engineering

Python · pandas · PostgreSQL · Batch Ingestion · Validation · Transactional Loading

### Data Modeling

Domain Modeling · Relational Modeling · Historical Modeling · Grain Definition

### Analytics

SQL · Dimensional Modeling · Cohort Analysis · Retention · Conversion · Product Analytics

### Quality

pytest · Data Quality Rules · Reconciliation · Integrity Validation

### Business Intelligence

Power BI · Serving Views · Semantic Modeling · Dashboard Storytelling

### Machine Learning

Python - pandas - scikit-learn - Logistic Regression - Feature Engineering - Model Evaluation

---

## Human-Directed, AI-Assisted Development

AI was used extensively throughout the project to accelerate technical implementation, analytical translation, debugging, testing and documentation.

The workflow remained iterative and human-directed:

```text
Requirement / Business Question
        ↓
Discussion & Design
        ↓
AI-Assisted Implementation
        ↓
Local Execution
        ↓
Result / Error Review
        ↓
Correction & Iteration
        ↓
Validated Result
```

Business intent, requirements, review, local execution, interpretation and design decisions remained part of the development process.

AI assistance was especially significant during implementation-heavy stages such as Python and SQL development, pipeline design, validation logic, testing, debugging and analytical translation.

The project also served as a hands-on learning process in which implementation was repeatedly executed, inspected and refined locally rather than treated as generated code that was accepted without verification.

[Read more about the AI-assisted workflow](docs/deep-dive/ai_assisted_development.md)

---

## Explore the Project

### Core Story

- [Business & Data Model](docs/core/01_business_and_data_model.md)
- [Data Platform](docs/core/02_data_platform.md)
- [Analytics](docs/core/03_analytics.md)
- [Dashboard & Storytelling](docs/core/04_dashboard_and_storytelling.md)
- [Reliability & Validation](docs/core/05_reliability_and_validation.md)
- [Machine Learning Extension](ml/README.md)

### Deep Dive

- [Engineering Decisions](docs/deep-dive/engineering_decisions.md)
- [Build Journey](docs/deep-dive/build_journey.md)
- [Reproducibility](docs/deep-dive/reproducibility.md)
- [AI-Assisted Development](docs/deep-dive/ai_assisted_development.md)
- [Limitations & Future Roadmap](docs/deep-dive/limitations_and_roadmap.md)

### Reference

- [Glossary](docs/reference/glossary.md)
- [Data Lineage](docs/reference/data_lineage.md)
- [Schema Reference](docs/reference/schema_reference.md)
- [Metric Reference](docs/reference/metric_reference.md)

---

## Project Status

The initial Data Engineering, Analytics and Power BI platform was published as [v1.0.0](https://github.com/KerenGrab/saas-website-builder-data-platform/releases/tag/v1.0.0).

A reproducible M6 Paid Retention Machine Learning proof of concept was subsequently added to `main` in commit `a1ea017`. Its code, dataset, experiment report and setup instructions are available in [ml/](ml/README.md).

The ML extension is an offline retrospective experiment and does not modify the existing operational data pipeline.

---

## Reproduction Verification

A local fresh-clone reproduction verified the frozen data release, PostgreSQL loading, Data Quality checks, Serving Views, and automated tests. See the [reproduction verification report](docs/reproduction_verification.md) for the observed results, environment details, and testing limitations.
