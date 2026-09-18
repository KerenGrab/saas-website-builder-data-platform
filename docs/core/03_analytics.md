# Analytics

This section explains how the operational data platform was translated into business analytics.

The analytical work did not begin with SQL queries or dashboard visuals.

It began with a business question.

The project follows this analytical reasoning chain:

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
SQL Logic
        ↓
Serving Output
        ↓
Business Interpretation
```

This approach is intended to prevent technically valid queries from producing analytically incorrect answers.

---

## 1. From Business Questions to Analytics

The analytical layer was designed around realistic questions that a SaaS company might ask about:

- customer conversion
- paid retention
- product engagement
- paid vs product activity
- feature adoption
- churn
- website outcomes
- commercial transitions
- support and customer friction

The goal was not to calculate as many metrics as possible.

The goal was to define metrics whose business meaning is explicit and whose population, denominator and time context can be explained.

---

## 2. Why Analytical Definitions Come Before SQL

A query can run successfully while still answering the wrong question.

Before implementing a metric, the project therefore asks:

```text
Who belongs in the analysis?
        ↓
What does one row represent?
        ↓
What event or state counts?
        ↓
Which time window applies?
        ↓
What belongs in the denominator?
        ↓
Which historical state should be used?
```

Only after these decisions are defined is the analytical logic translated into SQL.

This separation between **definition** and **implementation** is a central design principle of the project.

---

## 3. Analytical Grain

Grain defines what a single analytical row represents.

Different business questions require different grains.

Representative analytical grains in the project include:

```text
Account × Journey

Account × Month

Account × Feature × Month

Website × Month

Website × Feature × Month

Account × Churn Occurrence
```

Choosing the wrong grain can cause:

- double counting
- duplicated joins
- incorrect denominators
- distorted aggregation
- ambiguous business meaning

For example, a Website-level metric should not automatically be interpreted as an Account-level metric because one Account may manage multiple Websites.

Grain is therefore treated as an explicit part of every analytical definition.

---

## 4. Population and Denominator

Many analytical mistakes happen because the denominator is chosen implicitly.

The project treats the denominator as a business decision.

For example, Feature Adoption should not necessarily be calculated as:

```text
Accounts Using Feature
----------------------
All Accounts
```

because some Accounts may not have been eligible to use the Feature.

A more meaningful structure may be:

```text
Accounts That Adopted
---------------------
Eligible Accounts
```

This requires the system to understand:

- Plan history
- Feature availability
- eligibility
- time context
- actual usage

The population and denominator are therefore documented before the metric is implemented.

---

## 5. Time Semantics

Time definitions are another major analytical concern.

Different metrics may depend on different concepts such as:

- calendar month
- month-end state
- exact anniversary
- rolling windows
- activation date
- conversion horizon
- observation window
- website live period
- historical Plan state
- partial months

Two results may both be valid if they use different time definitions.

For example:

```text
Retention at Month-End
        ≠
Retention at Exact Anniversary
```

The correct response is not automatically to choose one and discard the other.

The time contract should be documented so the reader understands what each result means.

---

## 6. Historical State in Analytics

Historical analysis must use the state that existed at the time being analyzed.

For example:

```text
Feature Activity
      ↓
Event Date
      ↓
Which Plan was active then?
      ↓
Was the Feature available then?
      ↓
Was the Account eligible then?
```

Using the Account's current Plan for historical activity may produce analytically incorrect results.

This is why the historical modeling described in the Business & Data Model directly affects the analytical layer.

---

## 7. Analytical Model

The project includes **seven analytical fact designs** supported by shared dimensions.

The seven documented analytical designs are:

| Analytical Fact Design | Intended Grain |
|---|---|
| First Paid Conversion Journey | Account × Journey |
| Product Activity Snapshot | Account × Month |
| Commercial Status Snapshot | Account × Month |
| Paid Churn Occurrence | Account × Churn Occurrence |
| Account Feature Activity Snapshot | Account × Feature × Month |
| Website Outcomes Snapshot | Website × Month |
| Website Feature Activity Snapshot | Website × Feature × Month |

The shared dimensions are:

```text
Date
Account
Plan
Website
Feature
```

These are analytical designs.

They should not be interpreted as a claim that seven physical fact tables were necessarily materialized in PostgreSQL.

The design documents the intended analytical grains and relationships.

---

## 8. Why Shared Dimensions Matter

Shared dimensions provide consistent analytical context across multiple questions.

For example, the same Account concept can participate in:

- conversion analysis
- retention analysis
- commercial status
- churn
- feature adoption

Likewise, Website and Feature dimensions can support multiple analytical paths.

A particularly important dimension is **Plan**.

Plan must be interpreted historically when the analytical question refers to past activity.

```text
Current Plan
     ≠
Plan Active at Historical Event Time
```

This prevents current commercial state from being incorrectly projected backward onto historical behavior.

---

## 9. Metric Contracts

Important metrics are defined through explicit analytical contracts.

A metric contract can include:

| Contract Element | Question |
|---|---|
| Business Question | What are we trying to understand? |
| Population | Which entities belong in the analysis? |
| Grain | What does one analytical row represent? |
| Event / State | What qualifies as the measured behavior? |
| Time Definition | When is the metric evaluated? |
| Denominator | What population forms the base? |
| Exclusions | Who or what should not count? |
| Caveats | What limits interpretation? |
| Output | What does the resulting value mean? |

This makes analytical assumptions visible rather than hiding them inside SQL.

Metric definitions are also summarized in the:

[Metric Reference](../reference/metric_reference.md)

---

## 10. Golden Paths

Several analyses are especially useful because they demonstrate the full path from business reasoning to implementation and business interpretation.

The primary Golden Paths are:

```text
1. First Paid Conversion

2. Paid Retention
   +
   Product vs Paid Activity

3. Eligibility-Aware Feature Adoption

4. Website Outcomes

5. Commercial Transitions
```

Each Golden Path is intended to follow:

```text
Business Question
      ↓
Required Data
      ↓
Population
      ↓
Grain
      ↓
Metric Contract
      ↓
SQL
      ↓
Serving View
      ↓
Validation
      ↓
Power BI
      ↓
Business Interpretation
```

Validation evidence and reference documentation are published in the repository. Standalone analytical SQL is not part of the current published artifact set under sql/30_analytics.

---

## 11. Golden Path — First Paid Conversion

### Business Question

How quickly do eligible Accounts convert to their first paid state after activation?

This question requires more than identifying paid subscriptions.

The analysis must define:

- the eligible Account population
- the activation reference point
- the first qualifying paid event
- conversion horizons
- Accounts that have not yet had enough observation time
- exclusions and censoring

Conceptually:

```text
Eligible Account
      ↓
Activation
      ↓
Observation Window
      ↓
First Paid Conversion?
      ↓
Conversion by Horizon
```

This analysis demonstrates why denominator and observation-window definitions must be explicit.

---

## 12. Golden Path — Paid Retention

### Business Question

After customers become paid, how many remain in the relevant paid state over time?

Retention requires explicit decisions about:

- cohort definition
- start point
- evaluation dates
- paid state
- month-end vs anniversary semantics
- observation availability

Conceptually:

```text
Paid Cohort
    ↓
Retention Evaluation Point
    ↓
Paid State at That Time
    ↓
Retained / Eligible Cohort
```

The project preserves different time interpretations rather than silently treating them as equivalent.

---

## 13. Product vs Paid Activity

Payment and product activity describe different dimensions of customer health.

An Account may be:

```text
Paid + Product Active

Paid + Product Inactive

Not Paid + Product Active

Not Paid + Product Inactive
```

The purpose of this analysis is not simply to calculate another retention rate.

It is to identify cases in which commercial state and product engagement do not align.

This distinction can support questions about:

- customer health
- engagement risk
- retention
- reactivation
- product value

The exact Product Active definition must remain tied to its validated analytical contract.

---

## 14. Golden Path — Eligibility-Aware Feature Adoption

### Business Question

Among Accounts that could use a Feature, how many actually adopted it?

This requires several distinct concepts.

```text
Feature Exists
      ↓
Available Under Plan?
      ↓
Account Eligible?
      ↓
Feature Enabled?
      ↓
Feature Used?
```

These concepts should not be collapsed.

For example:

```text
Eligible
    ≠
Enabled
    ≠
Used
```

The denominator therefore needs to represent **opportunity to adopt**, rather than simply all Accounts in the system.

This analytical path demonstrates the connection between:

- historical Plan state
- entitlement
- feature enablement
- product activity
- analytical denominator design

---

## 15. Golden Path — Website Outcomes

### Business Question

What is happening on the Websites created by SaaS customers?

The Website Outcomes analysis focuses on audience and engagement signals such as:

- sessions
- page views
- form submissions
- friction events
- visitor activity
- engagement depth
- comments
- ratings

The analytical design uses Website-level historical activity before creating aggregated outputs for dashboard consumption.

A key distinction is:

```text
Website × Month Analytical Grain
              ↓
Monthly Serving Output
```

The serving grain does not need to be identical to the lower analytical grain.

This should be documented explicitly.

---

## 16. Golden Path — Commercial Transitions

### Business Question

How do Accounts move between commercial states and Plans?

Examples may include:

```text
Free → Standard

Standard → Higher Plan

Paid → Cancelled

Cancelled → Reactivated

Higher Plan → Lower Plan
```

This analysis distinguishes between:

- transition events
- distinct Accounts
- source Plan
- destination Plan
- transition type

A transition count is therefore not automatically equivalent to a customer count.

One Account may generate more than one commercial transition.

---

## 17. Supporting Analytical Areas

Not every useful metric needs to become a primary Golden Path.

Supporting analytical areas include concepts such as:

```text
Paid Churn
Support Activity
Ratings
Locked Feature Attempts
```

These analyses can provide additional context to the main customer, product and website stories.

These supporting areas are connected to the relevant dashboard and metric documentation where they are part of the current published scope.

---

## 18. SQL as Analytical Implementation

SQL is the implementation layer for analytical definitions.

The project does not treat a complex query as evidence of good analysis by itself.

The expected sequence is:

```text
Definition
    ↓
SQL Implementation
    ↓
Validation
    ↓
Interpretation
```

A technically sophisticated query can still be incorrect if:

- the population is wrong
- the denominator is wrong
- the grain is wrong
- historical state is ignored
- the time boundary is inconsistent

SQL therefore follows the analytical contract.

It does not define the contract by itself.

---

## 19. Analytical Layer to Serving Layer

The analytical results are not connected to Power BI arbitrarily.

The project uses a serving layer between analytical logic and the dashboard.

```text
Operational PostgreSQL
        ↓
Analytical Logic
        ↓
Metric Contract
        ↓
SQL
        ↓
Serving View
        ↓
Power BI
```

Serving views provide a controlled interface for dashboard consumption.

They help preserve:

- grain
- metric meaning
- aggregation rules
- denominator logic
- expected output structure

This reduces the risk that dashboard logic silently changes the analytical definition.

---

## 20. Serving Grain vs Analytical Grain

The serving layer may intentionally aggregate analytical data.

For example:

```text
Website × Month
Analytical Grain
      ↓
Aggregate Across Websites
      ↓
Month-Level Serving Output
```

The grain of the serving view must therefore be documented independently.

This prevents readers from assuming that the Power BI input has the same grain as the underlying analytical model.

---

## 21. Analytics and Business Interpretation

A metric is not the end of the analytical process.

The project connects results back to the original business question.

The intended flow is:

```text
Business Problem
      ↓
Metric
      ↓
Observed Result
      ↓
Context
      ↓
Interpretation
      ↓
Decision Support
```

The analysis is designed to provide evidence and context for decision-making.

It is not intended to automatically prescribe what a manager or product team should decide.

---

## 22. AI-Assisted Analytical Implementation

AI was used extensively to accelerate the technical implementation of the analytical layer.

The process typically followed:

```text
Business Question
        ↓
Joint Analytical Reasoning
        ↓
Population / Grain / Denominator / Time
        ↓
Explicit Metric Definition
        ↓
AI-Assisted SQL / Python Implementation
        ↓
Local Execution
        ↓
Result Review
        ↓
Corrections & Validation
```

AI assistance was especially useful for:

- translating analytical definitions into SQL
- generating complex queries
- supporting Python-based investigation
- debugging SQL
- proposing validation queries
- exploring alternative implementations
- accelerating iteration

The analytical reasoning did not begin with generated SQL.

Business meaning, populations, grains, denominators and time semantics were discussed before or alongside implementation.

The results were then executed and reviewed locally.

More detail is available in:

[AI-Assisted Development](../deep-dive/ai_assisted_development.md)

---

## 23. Analytical Traceability

An important goal of the repository is to make each major analytical result traceable.

The intended lineage is:

```text
Business Question
        ↓
Source Data
        ↓
Operational Tables
        ↓
Analytical Grain
        ↓
Metric Contract
        ↓
SQL
        ↓
Serving View
        ↓
Validation Evidence
        ↓
Dashboard Visual
        ↓
Business Interpretation
```

The repository reference for this mapping is:

[Data Lineage](../reference/data_lineage.md)

---

## 24. Results and Evidence

The project contains documented historical analytical results.

Published numerical claims should be traceable to:

- the exact metric definition
- the relevant SQL
- the serving output
- validation evidence
- the reference project version

For that reason, this page emphasizes analytical definitions and structure rather than presenting unsupported headline numbers.

Validated reference results are maintained in the analytics evidence under evidence/reference-results/analytics/.

---

## 25. From Analytics to Dashboard

The analytical layer provides meaning.

The serving layer provides controlled outputs.

Power BI provides the presentation and decision-support interface.

```text
Business Question
      ↓
Analytical Definition
      ↓
SQL
      ↓
Serving Layer
      ↓
Power BI
      ↓
Business Interpretation
```

The next section explains how these analytical results were translated into a three-page dashboard.

[Continue to Dashboard & Storytelling](04_dashboard_and_storytelling.md)

---

## 26. Related Documentation

### Core Story

- [Business & Data Model](01_business_and_data_model.md)
- [Data Platform](02_data_platform.md)
- [Dashboard & Storytelling](04_dashboard_and_storytelling.md)
- [Reliability & Validation](05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [AI-Assisted Development](../deep-dive/ai_assisted_development.md)
- [Build Journey](../deep-dive/build_journey.md)

### Reference

- [Metric Reference](../reference/metric_reference.md)
- [Data Lineage](../reference/data_lineage.md)
- [Schema Reference](../reference/schema_reference.md)

---

## Current Documentation Status

The analytical reasoning, analytical model and primary Golden Paths are documented here.

Serving definitions and validated numerical reference results are maintained in repository artifacts. Standalone analytical SQL under sql/30_analytics is not part of the current published artifact set.
