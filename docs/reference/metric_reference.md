# Metric Reference

This document provides a structured reference for the main analytical metrics used in the SaaS Website Builder Data Platform.

It is intended as a metric lookup document rather than a narrative analytics guide.

The central principle is:

```text
Metric Name
    ≠
Metric Definition
```

A metric is only meaningful when its analytical contract is explicit.

The project therefore defines metrics through concepts such as:

```text
Business Question
        ↓
Population
        ↓
Grain
        ↓
Time Semantics
        ↓
Numerator / Event
        ↓
Denominator
        ↓
Exclusions
        ↓
Output
        ↓
Interpretation
```

Exact SQL implementations, validated result values and evidence links will be connected after canonical analytical artifacts are selected and verified.

---

# 1. Metric Contract Structure

Each important metric should eventually be documented using the following structure.

```text
Metric:
<name>

Business Question:
<what decision or investigation this metric supports>

Population:
<who or what is eligible to participate>

Grain:
<what one analytical row represents>

Time Definition:
<how time is evaluated>

Numerator / Event:
<what is counted>

Denominator:
<base population if applicable>

Exclusions:
<what is intentionally removed>

Historical Context:
<which historical states are required>

Output:
<rate / count / state / distribution>

Interpretation:
<what the result means>

Caveats:
<what the result does not mean>

Implementation:
<canonical SQL — to be linked>

Evidence:
<reference result — to be linked>
```

Not every metric requires every field.

For example, an event count may not require a denominator.

---

# 2. Metric Families

The current analytical layer can be grouped into several business areas:

```text
Customer Lifecycle
        │
        ├── First Paid Conversion
        ├── Paid Retention
        └── Paid Churn

Product Engagement
        │
        ├── Product Activity
        ├── Product vs Paid Activity
        └── Feature Adoption

Website Outcomes
        │
        ├── Sessions
        ├── Page Views
        ├── Forms
        ├── Friction
        ├── Engagement
        └── Feedback

Product & Commercial Signals
        │
        ├── Locked Feature Attempts
        ├── Support Activity
        └── Commercial Transitions
```

These metric families correspond to different analytical populations and should not be mixed without an explicit reason.

---

# 3. First Paid Conversion

## Business Question

> How many eligible Accounts reach their first qualifying paid state within a defined period after the journey starting point?

First Paid Conversion is intended to describe movement from an eligible starting population into the customer's first qualifying paid state.

---

## Population

The population consists of Accounts that satisfy the documented eligibility conditions for the conversion journey.

The final physical population definition will be linked to the canonical analytical SQL.

Important principle:

```text
Conversion Denominator
≠
Every Account in the Database
```

The denominator must follow the defined journey population.

---

## Grain

```text
Account × Journey
```

One analytical row represents one Account's conversion journey under the defined contract.

---

## Starting Point

The conversion clock begins from a defined starting condition.

The exact source field and implementation will be documented from the canonical analytical model.

The important requirement is that the starting point is explicit and consistent across all conversion horizons.

---

## Conversion Event

The numerator represents Accounts that reach their **first qualifying paid state** according to the metric contract.

Later paid events should not be interpreted as additional first conversions for the same journey.

---

## Conversion Horizons

The project evaluates conversion across defined horizons such as:

```text
30 days
60 days
90 days
180 days
```

Each horizon answers:

> Did the Account convert within this amount of time from the journey starting point?

---

## Denominator

Conceptually:

```text
Accounts Eligible for the Conversion Journey
```

The denominator is not simply all Accounts.

---

## Numerator

Conceptually:

```text
Eligible Accounts
whose first qualifying paid event
occurs within the selected horizon
```

---

## Conceptual Formula

```text
Accounts Converted Within Horizon
---------------------------------
Eligible Journey Accounts
```

---

## Time Semantics

This metric depends on elapsed time from the Account-specific journey starting point.

It is therefore different from a simple calendar-month conversion rate.

---

## Caveats

A conversion rate should not be interpreted without knowing:

- the eligible population
- the starting point
- the paid-state definition
- the conversion horizon
- observation availability

Accounts without sufficient observation time may require special treatment depending on the final contract.

---

## Golden Path

```text
Business Question
        ↓
Eligible Accounts
        ↓
Journey Start
        ↓
First Paid Event
        ↓
Conversion Horizon
        ↓
Conversion Result
        ↓
Serving Output
        ↓
Power BI
```

---

## Implementation Status

```text
Analytical definition:
documented

Canonical SQL:
to be linked

Reference result:
to be linked

Evidence:
to be linked
```

---

# 4. Paid Retention

## Business Question

> After an Account enters the qualifying paid population, does it remain in the qualifying paid state at later evaluation points?

---

## Population

A defined paid cohort.

The cohort is established according to the paid-entry rules of the analytical contract.

---

## Grain

The core analytical interpretation is based on:

```text
Account × Cohort / Evaluation Point
```

The exact physical implementation may use Account-month snapshots or supporting structures.

---

## Cohort

A cohort groups Accounts according to a shared qualifying paid entry condition.

The cohort definition must remain stable when comparing retention points.

---

## Evaluation Points

Representative retention horizons include:

```text
M1
M3
M6
M12
```

The exact time semantics must be documented.

---

## Numerator

Conceptually:

```text
Cohort Accounts
that remain in the qualifying paid state
at the evaluation point
```

---

## Denominator

Conceptually:

```text
Eligible Accounts in the original paid cohort
```

The denominator should not silently change to only Accounts that are currently visible in a filtered reporting period unless the metric contract explicitly requires that behavior.

---

## Conceptual Formula

```text
Retained Paid Cohort Accounts
-----------------------------
Original Eligible Paid Cohort
```

---

## Time Semantics

Retention is especially sensitive to time definition.

For example:

```text
Month-End Retention
```

and:

```text
Exact-Anniversary Retention
```

can both be valid while producing different results.

The project therefore treats time semantics as part of the metric contract.

---

## Observation Availability

An Account may not have enough history to be evaluated at a later retention horizon.

The final implementation must distinguish between:

```text
Observed and Not Retained
```

and:

```text
Not Yet Fully Observable
```

where applicable.

---

## Interpretation

Paid Retention describes persistence of the defined commercial state.

It does not automatically describe:

- product engagement
- Website activity
- customer satisfaction

Those require separate signals.

---

## Golden Path

```text
Paid Entry
    ↓
Cohort
    ↓
Evaluation Time
    ↓
Historical Commercial State
    ↓
Retained?
    ↓
Retention Output
```

---

# 5. Product Activity

## Business Question

> Is an Account meaningfully active in the SaaS product during the relevant analytical period?

---

## Population

Accounts eligible to be evaluated for product activity under the analytical contract.

---

## Typical Grain

```text
Account × Month
```

---

## Definition

Product Activity is derived from qualifying activity rather than simply from the existence of an Account.

The exact activity events and thresholds belong to the canonical metric contract.

---

## Interpretation

Product Activity represents product engagement.

It should not be treated as equivalent to commercial status.

Therefore:

```text
Product Active
≠
Paid
```

---

# 6. Product vs Paid Activity

## Business Question

> Does commercial status align with actual product engagement?

This comparison combines two independently defined dimensions:

```text
Commercial Status
+
Product Activity
```

---

## Typical Grain

```text
Account × Month
```

---

## Core States

The comparison can produce states such as:

```text
Paid + Product Active

Paid + Product Inactive

Not Paid + Product Active

Not Paid + Product Inactive
```

---

## Why the Metric Exists

Commercial status alone does not describe engagement.

Product activity alone does not describe the customer's commercial relationship.

The combination can reveal useful mismatch populations.

---

## Potential Interpretation

Examples of questions supported by the metric include:

```text
Are paying Accounts actually using the product?

Are commercially inactive Accounts still showing activity?

Where do commercial and behavioral states diverge?
```

These are investigation signals rather than automatic conclusions.

---

## Historical Requirement

Commercial and product state should be aligned to the same analytical period.

Using today's paid state to classify historical product activity would create temporal inconsistency.

---

# 7. Paid Churn

## Business Question

> When does an Account leave the qualifying paid state under the project's churn definition?

---

## Grain

The analytical design includes:

```text
Account × Churn Occurrence
```

One Account may potentially generate more than one commercial lifecycle event over time if reactivation is allowed.

---

## Churn Event

Paid Churn represents a qualifying commercial transition out of paid status.

The exact qualifying states will be linked to the canonical analytical logic.

---

## Important Distinction

```text
Churn Event Count
≠
Distinct Accounts Ever Churned
```

A repeated lifecycle can produce multiple qualifying events.

---

## Interpretation

Paid Churn describes commercial-state loss.

It should not automatically be interpreted as:

```text
Product Inactivity
```

because commercial and product states are separate dimensions.

---

# 8. Feature Eligibility

## Business Question

> Did an Account have the opportunity to use a particular Feature at the relevant time?

Feature Eligibility is a prerequisite for meaningful Feature Adoption analysis.

---

## Typical Grain

```text
Account × Feature × Month
```

or another defined Account-feature-time grain.

---

## Historical Inputs

Eligibility may require:

```text
Account
+
Historical Plan
+
Feature
+
Observation Time
```

---

## Important Distinction

```text
Eligible
≠
Enabled
≠
Used
```

An Account may be eligible without using the Feature.

---

# 9. Feature Enablement

## Business Question

> Was a Feature enabled for the relevant entity during the analytical context?

Enablement represents configuration or availability state.

It should not be treated as evidence of actual use.

---

## Important Distinction

```text
Enabled
≠
Adopted
```

A Feature can be available but unused.

---

# 10. Feature Usage

## Business Question

> Was qualifying Feature activity observed during the relevant analytical period?

Usage represents observed product behavior.

The exact event or activity rule belongs to the canonical implementation.

---

# 11. Feature Adoption

## Business Question

> Among Accounts that had the opportunity to use a Feature, how many actually adopted it?

This is one of the project's main examples of denominator-sensitive analytics.

---

## Population

Accounts eligible for the Feature during the relevant analytical context.

---

## Typical Grain

```text
Account × Feature × Month
```

for the underlying analytical design.

Dashboard serving grain may be more aggregated.

---

## Numerator

Conceptually:

```text
Eligible Accounts
with qualifying Feature usage
```

---

## Denominator

Conceptually:

```text
Accounts Eligible for the Feature
```

---

## Conceptual Formula

```text
Eligible Accounts That Adopted
------------------------------
Eligible Accounts
```

---

## Why Eligibility Matters

A weaker formula would be:

```text
Accounts Using Feature
----------------------
All Accounts
```

but this can penalize a Feature for Accounts that never had access to it.

The project's metric therefore treats the denominator as part of the business definition.

---

## Historical Requirement

Eligibility may change when Plan or access conditions change.

Therefore, current Plan state should not automatically be used for historical Feature Adoption.

---

## Golden Path

```text
Feature
   ↓
Historical Plan
   ↓
Eligibility
   ↓
Observed Usage
   ↓
Adoption
   ↓
Serving Output
   ↓
Power BI
```

---

# 12. Website Feature Activity

## Business Question

> How are Features being used at Website level rather than only Account level?

---

## Analytical Grain

```text
Website × Feature × Month
```

---

## Important Distinction

```text
Account Feature Activity
≠
Website Feature Activity
```

An Account may own multiple Websites.

Website-level activity therefore provides a more detailed product-use perspective.

---

# 13. Sessions

## Business Question

> How much audience visit activity occurs across customer Websites?

---

## Primary Entity

```text
Session
```

---

## Typical Serving Context

Website and time dimensions may be used to aggregate Session activity.

---

## Interpretation

Session count describes visit volume.

It does not by itself describe engagement quality or success.

---

# 14. Page Views

## Business Question

> How much page-consumption activity occurs within customer Websites?

---

## Primary Event

```text
page_viewed
```

---

## Interpretation

Page Views describe content consumption volume.

They should be interpreted together with metrics such as:

- Sessions
- Pages per Session
- Session Duration

when analyzing engagement.

---

# 15. Form Submissions

## Business Question

> How often do Website audiences complete a qualifying form action?

---

## Primary Event

Conceptually:

```text
form_submitted
```

---

## Interpretation

Form submissions may represent meaningful audience action.

The business meaning depends on the Website context.

---

# 16. Friction Events

## Business Question

> How often do audience interactions encounter a qualifying failure or friction condition?

---

## Primary Event

Conceptually:

```text
failure_friction
```

---

## Interpretation

Friction volume should be interpreted relative to audience scale.

Raw friction counts alone can be misleading when comparing Websites or periods with very different traffic.

---

# 17. Friction per 100 Sessions

## Business Question

> How much friction occurs relative to visit volume?

---

## Numerator

```text
Qualifying Friction Events
```

---

## Denominator

```text
Sessions
```

---

## Conceptual Formula

```text
Friction Events
---------------
Sessions
× 100
```

---

## Interpretation

This normalizes friction by audience volume.

It allows more meaningful comparison between periods or Websites than raw friction counts alone.

---

## Caveat

The metric does not automatically indicate root cause.

A high value is a signal for investigation.

---

# 18. Pages per Session

## Business Question

> How much page-level interaction occurs during an average Session?

---

## Numerator

```text
Page Views
```

---

## Denominator

```text
Sessions
```

---

## Conceptual Formula

```text
Page Views
----------
Sessions
```

---

## Interpretation

Higher Pages per Session may indicate deeper navigation, but its business meaning depends on context.

More pages can represent either useful engagement or difficulty finding information.

---

# 19. Session Duration

## Business Question

> How long do audience Sessions last under the documented Session Duration definition?

---

## Population

Sessions that satisfy the metric's final inclusion rules.

---

## Time Requirement

Session Duration depends on how Session start and end are defined.

The exact calculation will be connected to the canonical analytical SQL.

---

## Caveat

A longer Session should not automatically be interpreted as better.

Duration requires business context.

---

# 20. Comments

## Business Question

> How much explicit textual feedback is being provided by Website audiences or members?

---

## Signal Type

```text
Explicit Feedback
```

rather than behavioral activity.

---

## Interpretation

Comment volume can provide context around audience participation but does not automatically indicate positive or negative sentiment.

---

# 21. Ratings

## Business Question

> What structured feedback are Website audiences providing?

---

## Signal Type

```text
Explicit Feedback
```

---

## Analytical Form

Ratings may be represented through:

- count
- distribution
- average rating
- snapshot

depending on the relevant visual or analytical question.

---

## Filter Caveat

Rating visuals may require snapshot isolation so unrelated report filters do not accidentally redefine the intended population.

---

# 22. Website Outcomes

## Business Question

> What does audience behavior and feedback look like for each Website over time?

---

## Analytical Grain

```text
Website × Month
```

---

## Typical Components

Website Outcomes may combine signals such as:

```text
Sessions
Page Views
Form Submissions
Friction
Engagement
Comments
Ratings
```

These signals represent different dimensions and should not automatically be collapsed into one generic "success" score.

---

## Interpretation

The purpose of the Website Outcomes model is to provide a multidimensional view.

It does not prescribe one universal definition of Website success.

---

# 23. Locked Feature Attempts

## Business Question

> Are users attempting to use functionality that is unavailable under their current access conditions?

---

## Event Concept

```text
Attempt Feature
      ↓
Not Available
      ↓
Locked Feature Attempt
```

---

## Interpretation

Locked attempts can indicate:

- demand
- discovery
- plan mismatch
- frustration
- possible commercial opportunity

They should not automatically be interpreted as guaranteed upgrade intent.

---

# 24. Support Activity

## Business Question

> What level of customer-support interaction exists during the relevant analytical period?

---

## Primary Entity

```text
Support Request
```

---

## Interpretation

Support activity is a contextual operational signal.

It should not be treated as a standalone measure of customer satisfaction or customer health.

---

# 25. Commercial Transition

## Business Question

> How do Accounts move between commercial states or Plans over time?

---

## Event Grain

Conceptually:

```text
Account × Commercial Transition
```

---

## Transition Types

Representative categories include:

```text
Upgrade
Downgrade
Cancellation
Reactivation
```

The exact canonical classification logic will be linked to the analytical implementation.

---

## Important Distinction

```text
Transition Events
≠
Distinct Accounts
```

One Account may generate multiple commercial transitions.

---

# 26. Upgrade

A qualifying commercial transition to a higher Plan or commercial level according to the documented transition rules.

---

# 27. Downgrade

A qualifying commercial transition to a lower Plan or commercial level.

---

# 28. Cancellation

A qualifying transition out of the active commercial relationship according to the documented business rules.

Cancellation and analytical Paid Churn may be related but should not automatically be assumed to be identical definitions.

---

# 29. Reactivation

A qualifying return into an active or paid commercial state after a previous exit.

Reactivation means the customer lifecycle is not necessarily a single one-direction path.

Conceptually:

```text
Paid
 ↓
Exit
 ↓
Inactive / Non-Paid
 ↓
Reactivation
 ↓
Paid Again
```

---

# 30. Metric Grain Reference

The main analytical designs currently use grains such as:

| Analytical Area | Grain |
|---|---|
| First Paid Conversion | Account × Journey |
| Product Activity | Account × Month |
| Commercial Status | Account × Month |
| Paid Churn | Account × Churn Occurrence |
| Account Feature Activity | Account × Feature × Month |
| Website Outcomes | Website × Month |
| Website Feature Activity | Website × Feature × Month |

Grain describes what one analytical row represents.

Serving outputs may use a more aggregated grain.

---

# 31. Population Reference

Common analytical populations include:

```text
Eligible Journey Accounts

Paid Cohort Accounts

Product-Observable Accounts

Feature-Eligible Accounts

Active / Observable Websites

Website Sessions

Commercial Transition Events
```

Population should always be interpreted according to the metric contract.

---

# 32. Denominator Reference

Important denominator principles include:

```text
Conversion
→ eligible journey population
```

```text
Retention
→ original eligible cohort
```

```text
Feature Adoption
→ eligible population
```

```text
Friction Rate
→ relevant Sessions
```

A denominator should not be changed simply because a dashboard filter makes another denominator convenient.

---

# 33. Time Semantics Reference

Metrics in the project may use different time interpretations.

Examples include:

```text
Calendar Month

Month-End State

Exact Anniversary

Historical As-Of Date

Conversion Horizon

Observation Window

Rolling / Recent Activity Window
```

Time semantics are part of metric meaning.

---

# 34. Historical-State Requirement

Metrics requiring historical context should resolve state at the relevant analytical time.

Conceptually:

```text
Observation Date
      ↓
Historical State
      ↓
State Valid on That Date
```

This is especially important for:

- Plan
- subscription state
- paid status
- Feature eligibility
- Website live state

---

# 35. Partial Periods

A partial period contains less observation time than a complete period.

For example, the latest month in a dataset may not contain a full calendar month.

Therefore:

```text
Partial Month
≠
Automatically Comparable to Full Month
```

Dashboard interpretation should preserve this caveat.

---

# 36. Analytical Result vs Business Conclusion

A metric provides evidence.

It does not automatically produce the business decision.

For example:

```text
High Locked Feature Attempts
```

may support investigation into:

```text
Product Demand
Pricing
Packaging
Usability
Upgrade Opportunity
```

but the metric does not determine which explanation is correct.

---

# 37. Metric-to-SQL Relationship

The intended implementation flow is:

```text
Metric Contract
      ↓
Canonical SQL
      ↓
Validated Output
```

SQL should implement the metric definition.

The metric definition should not be reverse-engineered solely from whichever SQL query happens to exist.

---

# 38. Metric-to-Serving Relationship

A metric may be transformed again before Power BI consumes it.

Conceptually:

```text
Analytical Metric
      ↓
Serving Transformation
      ↓
Dashboard Input
```

The serving layer must preserve the intended:

- grain
- denominator
- time semantics
- aggregation rules

---

# 39. Metric-to-Visual Relationship

The complete chain is:

```text
Business Question
      ↓
Metric Contract
      ↓
SQL
      ↓
Serving Output
      ↓
Power BI Visual
      ↓
Business Interpretation
```

A visual should therefore be traceable back to the metric definition that produced it.

---

# 40. Metric Validation

A query executing successfully does not prove that the metric is correct.

Metric validation may consider:

```text
Population
Grain
Time Semantics
Denominator
Historical State
Exclusions
Expected Counts
Serving Behavior
```

This analytical validation is separate from ordinary SQL syntax correctness.

---

# 41. Reference Results

Validated numerical results will eventually be connected to this reference.

The intended format is:

```text
Metric
      ↓
Metric Contract
      ↓
Canonical SQL
      ↓
Reference Result
      ↓
Evidence Artifact
```

At the current documentation stage, result values are intentionally not duplicated here without their final evidence mapping.

---

# 42. Dashboard Mapping

The main metric families map broadly to the three Power BI pages.

```text
Page 1
Customer Lifecycle & Multi-Dimensional Health

→ First Paid Conversion
→ Paid Retention
→ Product vs Paid Activity
→ Feature Adoption
→ Paid Churn
```

```text
Page 2
Website Audience Activity,
Engagement & Feedback

→ Sessions
→ Page Views
→ Forms
→ Friction
→ Pages per Session
→ Session Duration
→ Comments
→ Ratings
```

```text
Page 3
SaaS Product & Strategy Signals

→ Feature Adoption
→ Locked Feature Attempts
→ Support Activity
→ Commercial Transitions
```

Some metrics may support more than one business story.

---

# 43. Planned Final Metric Reference

After canonical analytical SQL is selected, each priority metric will also include:

```text
Canonical SQL File
Serving View
Power BI Visual / Page
Reference Result
Evidence Location
Validation Status
```

This will transform the document from conceptual metric reference into a complete analytical traceability index.

---

# 44. Priority Golden Paths

The first complete metric-to-evidence mappings should focus on:

```text
First Paid Conversion

Paid Retention

Product vs Paid Activity

Eligibility-Aware Feature Adoption

Website Outcomes

Commercial Transitions
```

These provide broad coverage across:

```text
Customer Lifecycle
Product Engagement
Historical Logic
Website Analytics
Commercial Behavior
```

---

# 45. Current Reference Boundary

At this stage:

```text
Metric meaning
→ documented

Analytical grain
→ documented

Population principles
→ documented

Time-semantics principles
→ documented

Canonical SQL paths
→ pending selection

Reference values
→ pending evidence mapping

Power BI visual identifiers
→ pending final verification
```

This separation is intentional.

The reference should become more specific only when the underlying artifact has been verified.

---

## Related Documentation

### Core

- [Analytics](../core/03_analytics.md)
- [Dashboard & Storytelling](../core/04_dashboard_and_storytelling.md)
- [Reliability & Validation](../core/05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [Reproducibility](../deep-dive/reproducibility.md)

### Reference

- [Glossary](glossary.md)
- [Schema Reference](schema_reference.md)
- [Data Lineage](data_lineage.md)

### Repository

- [SQL](../../sql/README.md)
- [Evidence](../../evidence/README.md)

---

## Current Documentation Status

The main analytical concepts, populations, grains, denominator principles and time semantics are documented here.

Canonical SQL paths, validated result values, serving-view mappings and evidence links will be added after analytical artifact selection and release verification.