# Dashboard & Storytelling

This section explains how the analytical layer was translated into a business-facing Power BI dashboard.

The dashboard is not treated as the starting point of the analytical process.

It is the final presentation layer of a longer chain:

```text
Business Question
        ↓
Metric Definition
        ↓
Analytical Logic
        ↓
SQL
        ↓
Serving Layer
        ↓
Power BI
        ↓
Business Interpretation
```

The purpose of the dashboard is to make modeled and validated data understandable enough to support product, operational and managerial decision-making.

---

## 1. Why the Dashboard Exists

The project does not use Power BI simply to demonstrate visualization skills.

The dashboard was designed to answer realistic questions that a SaaS company might ask about:

- customer lifecycle
- conversion
- retention
- product engagement
- feature adoption
- website audience activity
- customer friction
- support activity
- commercial movement
- product opportunities

The central idea is:

> The dashboard is the point where technical data work becomes business-facing information.

The visual layer therefore depends on the definitions and validation performed earlier in the project.

---

## 2. From Analytics to Business Intelligence

Power BI is not connected directly to arbitrary operational tables.

The project uses an intermediate serving layer.

```text
Operational PostgreSQL
        ↓
Analytical Logic
        ↓
Metric Contracts
        ↓
SQL
        ↓
Serving Views
        ↓
Power BI Semantic Model
        ↓
Dashboard Visuals
```

This separation helps preserve:

- analytical grain
- metric meaning
- aggregation rules
- denominator logic
- time semantics

It also reduces the amount of analytical logic that needs to be recreated inside the dashboard.

---

## 3. Why a Serving Layer Matters

A dashboard should not silently redefine a metric.

For example, if Feature Adoption was analytically defined as:

```text
Adopted Eligible Accounts
-------------------------
Eligible Accounts
```

the visual layer should not accidentally divide adopted Accounts by all Accounts.

The serving layer therefore acts as a controlled interface between analytics and visualization.

Its role is to provide Power BI with data that already reflects the intended analytical meaning.

---

## 4. Dashboard Structure

The dashboard is organized into three business-oriented pages.

```text
Page 1
Customer Lifecycle & Multi-Dimensional Health

Page 2
Website Audience Activity, Engagement & Feedback

Page 3
SaaS Product & Strategy Signals
```

Each page answers a different family of business questions.

The goal is not to place every metric on one screen.

The goal is to give each page a clear analytical story.

---

# Page 1 — Customer Lifecycle & Multi-Dimensional Health

## 5. Purpose

The first page focuses on the commercial and product health of SaaS customers.

The central question is:

> Are customers progressing through a healthy lifecycle, and does their commercial relationship align with actual product engagement?

The page brings together signals such as:

- First Paid Conversion
- Paid Retention
- Product vs Paid Activity
- Feature Adoption
- Paid Churn

These metrics describe different dimensions of customer health.

They should not be interpreted as interchangeable.

---

## 6. Conversion

First Paid Conversion helps answer:

> How many eligible Accounts move from activation into their first paid state within a defined period?

The dashboard does not define the metric independently.

Its result depends on the analytical contract described in the Analytics section.

The visual therefore represents the final stage of:

```text
Eligible Population
        ↓
Activation
        ↓
Conversion Horizon
        ↓
First Paid Event
        ↓
Serving Output
        ↓
Power BI
```

---

## 7. Paid Retention

Paid Retention helps answer:

> After entering the paid population, how many Accounts remain in the relevant paid state over time?

Retention is sensitive to:

- cohort definition
- evaluation date
- time semantics
- observation availability

The dashboard should therefore be read together with the documented metric contract rather than as an isolated percentage.

---

## 8. Product vs Paid Activity

Commercial status and product activity describe different dimensions.

An Account may be:

```text
Paid + Product Active

Paid + Product Inactive

Not Paid + Product Active

Not Paid + Product Inactive
```

This comparison can reveal situations in which payment status and product engagement do not align.

Such mismatches may provide useful context for:

- retention discussions
- engagement analysis
- customer health
- reactivation
- product value investigation

The dashboard presents these signals as evidence for further investigation rather than as automatic business decisions.

---

## 9. Feature Adoption

Feature Adoption helps answer:

> Among Accounts that had the opportunity to use a Feature, how many actually adopted it?

The dashboard relies on the eligibility-aware analytical definition.

This means the visual should preserve distinctions such as:

```text
Eligible
    ≠
Enabled
    ≠
Used
```

This prevents a visually simple percentage from hiding an incorrect denominator.

---

# Page 2 — Website Audience Activity, Engagement & Feedback

## 10. Purpose

The second page shifts perspective.

Instead of looking primarily at SaaS customers, it focuses on what happens inside the Websites those customers manage.

The central question is:

> How are website audiences interacting with customer Websites?

The page combines several types of activity:

- sessions
- page views
- form submissions
- friction events
- engagement depth
- session duration
- comments
- ratings

This provides a more complete view than traffic volume alone.

---

## 11. Traffic and Activity

Metrics such as Sessions and Page Views help describe audience scale.

However, traffic alone does not necessarily represent successful engagement.

The page therefore combines volume with additional behavioral signals.

```text
Traffic
   +
Engagement
   +
Actions
   +
Friction
   +
Feedback
```

This produces a broader view of Website activity.

---

## 12. Engagement

Metrics such as:

- Pages per Session
- Session Duration

help describe how deeply audiences interact with Websites.

These measures provide additional context beyond raw visitor counts.

They can help distinguish:

```text
High Traffic
+
Low Engagement
```

from:

```text
High Traffic
+
Deeper Interaction
```

The dashboard provides the evidence.

Interpretation still depends on business context.

---

## 13. Forms and Friction

Form submissions can represent meaningful user actions.

Friction events represent the opposite type of signal.

For example:

```text
Audience Arrives
      ↓
Interacts
      ↓
Attempts Action
      ↓
Success or Friction
```

Viewing these metrics together can support investigation into Website experience and potential usability problems.

---

## 14. Comments and Ratings

Comments and Ratings provide explicit audience feedback.

These signals differ from behavioral activity.

A visitor can spend time on a Website without leaving direct feedback.

The dashboard therefore keeps:

```text
Behavioral Signals
        ≠
Explicit Feedback
```

Both perspectives can contribute to understanding Website outcomes.

---

## 15. Partial Periods

Time-based dashboard interpretation must account for incomplete periods.

If the latest month contains only partial data, it should not automatically be compared with a full previous month as though the observation windows were identical.

The dashboard documentation therefore needs to preserve partial-period caveats when relevant.

---

# Page 3 — SaaS Product & Strategy Signals

## 16. Purpose

The third page focuses on signals that may be useful for product and commercial discussions.

The central question is:

> What patterns in product usage, access limitations, support activity and commercial transitions may indicate opportunities or friction?

The page includes areas such as:

- Feature Adoption
- Locked Feature Attempts
- Support Activity
- Commercial Transitions

These metrics connect product behavior with commercial context.

---

## 17. Locked Feature Attempts

A locked Feature attempt represents a useful product signal.

Conceptually:

```text
User Attempts Feature
        ↓
Feature Not Available
        ↓
Locked Attempt
```

This does not automatically mean the customer should upgrade.

However, repeated locked attempts may indicate:

- demand for unavailable functionality
- plan mismatch
- pricing or packaging questions
- product discovery
- upgrade opportunity
- user frustration

The dashboard surfaces the signal.

It does not prescribe the decision.

---

## 18. Support Activity

Support activity provides operational context.

Support metrics can help investigate questions such as:

- Are support requests increasing?
- Are certain periods associated with more customer friction?
- Does support activity align with product or commercial signals?

Support information is therefore useful as a supporting indicator rather than a standalone measure of customer health.

---

## 19. Commercial Transitions

Commercial transitions show how Accounts move through Plan and subscription states.

Examples include:

```text
Upgrade
Downgrade
Cancellation
Reactivation
```

The dashboard distinguishes between:

- number of transition events
- number of distinct Accounts
- transition type
- source Plan
- destination Plan

This avoids interpreting every transition event as a unique customer.

---

## 20. Business Value and Decision Support

The analytics and dashboard were designed around realistic management and product questions, not around arbitrary metrics.

The intended flow is:

```text
Realistic Business Problem
        ↓
Question a Manager or Analyst Might Ask
        ↓
Relevant Data
        ↓
Metric Definition
        ↓
SQL & Serving Layer
        ↓
Dashboard Visual
        ↓
Evidence & Context
        ↓
Business Discussion / Decision Support
```

The dashboard can support discussions such as:

### Customer Lifecycle

- onboarding effectiveness
- conversion
- retention
- customer engagement

### Website Experience

- audience behavior
- engagement
- friction
- feedback

### Product Strategy

- feature demand
- adoption
- plan limitations
- support pressure
- commercial movement

The dashboard is designed to support decisions with evidence.

It is not designed to automatically determine what decision should be made.

---

## 21. Metric-to-Visual Traceability

Every important visual should ultimately be traceable back to its analytical definition.

The intended lineage is:

```text
Business Question
        ↓
Metric Contract
        ↓
SQL
        ↓
Serving View
        ↓
Power BI Visual
        ↓
Business Interpretation
```

For example:

```text
Feature Adoption Question
        ↓
Eligibility Definition
        ↓
Account × Feature Logic
        ↓
Serving Output
        ↓
Feature Adoption Visual
```

This traceability is documented in:

[Data Lineage](../reference/data_lineage.md)

---

## 22. Dashboard Design Decisions

Dashboard design affects metric meaning.

The project therefore treats visual configuration as part of analytical correctness.

Examples of important design considerations include:

- filter isolation
- date filtering
- total-card behavior
- percentage formatting
- feature selector behavior
- rating snapshot isolation
- aggregation behavior

A dashboard filter should not silently change a metric denominator or analytical population unless that behavior is intentional.

---

## 23. Filter Context

Power BI visuals operate within filter context.

This means a seemingly small interaction can change the analytical meaning of a visual.

For example:

```text
Feature Selector
      ↓
Should affect Feature visuals
```

but it may not be appropriate for the same selector to change unrelated lifecycle metrics.

The dashboard therefore required attention to which filters should affect which visuals.

---

## 24. Snapshot Isolation

Some metrics represent a snapshot rather than a continuous time series.

For example, a Rating distribution may represent a specific analytical snapshot.

If a general date filter modifies that visual incorrectly, the result may no longer reflect the intended metric.

This is why filter isolation and metric-specific context are part of dashboard validation.

---

## 25. Percentages and Totals

Formatting is not only cosmetic.

A value such as:

```text
0.4609
```

may need to be presented as:

```text
46.09%
```

Likewise, a Total card must represent the intended business total rather than the visible sum of an incorrectly filtered visual.

Dashboard validation therefore includes both:

- analytical correctness
- presentation correctness

---

## 26. Dashboard Gallery

The repository includes clean exports of all three Power BI pages under `assets/dashboard/`.

Published dashboard export structure:

```text
Page 1
Customer Lifecycle & Multi-Dimensional Health

Page 2
Website Audience Activity, Engagement & Feedback

Page 3
SaaS Product & Strategy Signals
```

Each dashboard image should be accompanied by a short explanation of:

- the business question
- important metrics
- population or context
- interpretation
- relevant caveat

The main README links to the dashboard documentation; the exported dashboard pages remain available under `assets/dashboard/`.

---

## 27. Power BI Project Source

The repository includes one verified Power BI Project source at `dashboard/powerbi/SaaS_Analytics_Dashboard.pbip`.

The published Power BI Project includes:

```text
Report
+
Semantic Model
```

Local Power BI state and cache files should not be published.

The canonical Power BI source is `dashboard/powerbi/SaaS_Analytics_Dashboard.pbip`, with its Report and Semantic Model stored alongside it.

---

## 28. AI-Assisted Dashboard Development

AI was used extensively during dashboard development and troubleshooting.

Assistance included areas such as:

- organizing dashboard pages
- connecting serving outputs to visuals
- Power BI project structure
- filtering logic
- aggregation problems
- percentage formatting
- debugging visual behavior
- proposing implementation corrections

The workflow remained iterative.

```text
Dashboard Requirement
        ↓
AI-Assisted Implementation / Suggestion
        ↓
Open Locally in Power BI
        ↓
Visual Inspection
        ↓
Screenshot / Result Review
        ↓
Identify Problem
        ↓
Correction
        ↓
Reopen / Refresh / Validate
```

Local inspection was important because dashboard behavior cannot be fully validated from source text alone.

The development process included repeated visual review of actual Power BI output.

More detail is available in:

[AI-Assisted Development](../deep-dive/ai_assisted_development.md)

---

## 29. Dashboard Boundaries

The dashboard should be interpreted according to the scope of the project.

It is based on:

- synthetic SaaS data
- locally implemented analytics
- documented serving outputs
- a local Power BI environment

It is not evidence of:

- a live production SaaS company
- real customer behavior
- real commercial performance
- production-scale BI deployment

The dashboard demonstrates analytical and storytelling methodology using a realistic synthetic business environment.

---

## 30. From Dashboard to Validation

A polished dashboard is not sufficient evidence that its numbers are correct.

The project therefore validates the layers underneath the visuals.

```text
Source
    ↓
Database
    ↓
Analytical Logic
    ↓
Serving View
    ↓
Dashboard
```

The next section explains the reliability and validation mechanisms used across this chain.

[Continue to Reliability & Validation](05_reliability_and_validation.md)

---

## 31. Related Documentation

### Core Story

- [Business & Data Model](01_business_and_data_model.md)
- [Data Platform](02_data_platform.md)
- [Analytics](03_analytics.md)
- [Reliability & Validation](05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [Build Journey](../deep-dive/build_journey.md)
- [AI-Assisted Development](../deep-dive/ai_assisted_development.md)

### Reference

- [Metric Reference](../reference/metric_reference.md)
- [Data Lineage](../reference/data_lineage.md)

---

## Current Documentation Status

The dashboard story, page structure, business role and validation principles are documented here.

Clean dashboard exports, the canonical Power BI Project source, Data Lineage documentation and verified serving references are maintained in the repository.
