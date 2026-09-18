# Business & Data Model

This section explains how the fictional Website Builder SaaS business was translated into a structured data model.

The goal was not to begin with tables and columns.

The project first defined the business world, the actors operating within it, the relationships between them, the business rules that connect them and the historical information required to answer realistic analytical questions.

The modeling process followed this direction:

```text
Business Idea
      ↓
Actors & Business Processes
      ↓
Conceptual Entities
      ↓
Relationships & Ownership
      ↓
Business Rules
      ↓
Historical Requirements
      ↓
Logical Relational Model
      ↓
PostgreSQL Implementation
```

---

## 1. Business Context

The project models a fictional **Website Builder SaaS company**.

The platform allows customers to create and manage websites while the SaaS company operates the product, manages subscriptions and features, and observes how customers and website audiences use the system.

This creates three connected perspectives:

```text
SaaS Company
      ↓
Website Owner / Customer
      ↓
Website
      ↓
Visitors & Members
```

Each perspective produces different types of data.

The SaaS company needs information about:

- customers
- subscriptions
- plans
- payments
- product usage
- features
- support activity
- commercial lifecycle changes

Website owners manage:

- websites
- pages
- content
- enabled functionality
- members
- audience activity

Website audiences generate:

- visits
- sessions
- interactions
- comments
- ratings
- forms and other engagement signals

The data model was therefore designed to represent both the **SaaS product itself** and the **activity occurring inside customer websites**.

---

## 2. Business Ecosystem

A central modeling decision was to treat the system as an ecosystem rather than as a single user-product relationship.

At a high level:

```text
Visitors / Website Members
          ↓
       Website
          ↓
Website Owner / SaaS Customer
          ↓
     SaaS Company
```

Information also flows back through the system.

Website activity creates product and business signals that can help the SaaS company understand:

- customer engagement
- product adoption
- website outcomes
- support needs
- subscription behavior
- opportunities for product improvement

The conceptual ecosystem is broader than the current implementation.

Some parts represent the **business vision**, while the repository documents separately which components are implemented and measured in the current project.

---

## 3. Domain Hierarchy

The domain contains several actors that may appear similar at first but represent different concepts.

One of the most important modeling decisions was to keep these identities separate.

```text
Account
│
├── SaaS Users
│
└── Websites
      │
      ├── Pages
      ├── Content
      ├── Website Members
      └── Visitor Activity
```

This hierarchy prevents different populations from being accidentally treated as the same type of user.

---

## 4. Key Identity Distinctions

### Account

An **Account** represents the SaaS customer organization or customer-level business entity.

It is the main unit for customer lifecycle, subscription and commercial analysis.

An Account can be associated with:

- SaaS Users
- Websites
- Plans and Subscriptions
- Payments
- Feature activity
- Support requests

---

### SaaS User

A **SaaS User** is a person who operates the Website Builder product on behalf of an Account.

This actor belongs to the customer-management side of the system.

A SaaS User is not the same thing as somebody visiting one of the customer's websites.

---

### Website

A **Website** is a digital property created and managed by an Account.

An Account may manage multiple Websites.

Website-level analysis can therefore differ from Account-level analysis.

A Website may contain:

- Pages
- Content Items
- enabled functionality
- members
- visitor sessions
- interaction events
- comments
- ratings

---

### Website Member

A **Website Member** is a registered or recognized user of a customer's Website.

Website Members belong to the audience side of the customer's website.

They are different from SaaS Users, who operate the Website Builder platform itself.

---

### Visitor

A **Visitor** represents somebody interacting with a Website.

A Visitor does not necessarily need to be a registered Website Member.

This distinction allows the model to represent both anonymous and known website activity.

---

## 5. Why These Identities Are Separate

The distinction can be summarized as:

```text
Account
   ≠
SaaS User
   ≠
Website Member
   ≠
Visitor
```

These concepts represent different actors and different analytical populations.

For example:

- Account-level retention should not be measured using Visitor records.
- Website audience engagement should not use SaaS Users as its population.
- SaaS product activity belongs to the customer side of the platform.
- Website activity belongs to the audience side of customer-owned websites.

Separating these concepts early prevents population mixing later in SQL and analytics.

---

## 6. Core Domain Entities

The project contains a larger logical schema, but the main business concepts can be summarized through the following entity groups.

| Entity | Business Purpose |
|---|---|
| Account | Represents the SaaS customer organization |
| SaaS User | Represents a person managing the SaaS product for an Account |
| Website | Represents a website created and managed by an Account |
| Page | Represents a page belonging to a Website |
| Content Item | Represents content managed within the website |
| Feature | Represents product functionality offered by the SaaS platform |
| Website Member | Represents a registered user of a customer Website |
| Visitor | Represents a website audience identity |
| Session | Represents a period of website activity |
| Interaction Event | Represents an action occurring during product or website activity |
| Comment | Represents audience feedback |
| Rating | Represents structured audience feedback |
| Plan | Represents a commercial SaaS plan |
| Subscription | Represents the commercial relationship between an Account and a Plan |
| Payment | Represents payment activity |
| Support Request | Represents customer support activity |

The complete technical schema is documented separately in the [Schema Reference](../reference/schema_reference.md).

---

## 7. Relationships and Ownership

Relationships were modeled according to business meaning rather than only database convenience.

For example:

```text
Account
   │
   ├── owns / manages → Website
   │
   ├── contains → SaaS Users
   │
   ├── has → Subscription History
   │
   └── generates → Commercial Activity
```

And on the website side:

```text
Website
   │
   ├── contains → Pages
   ├── contains → Content
   ├── serves → Visitors
   ├── may register → Website Members
   └── generates → Sessions & Interaction Events
```

The ownership relationship between Account and Website is especially important.

The **Account** is the SaaS customer.

The **Website** is an asset managed by that customer.

One Account may therefore own or manage multiple Websites.

---

## 8. Business Rules

The model includes business rules that reflect how the fictional platform operates.

Examples include:

- An Account may manage multiple Websites.
- A Website belongs to an Account.
- A Visitor does not necessarily need to be a Website Member.
- A SaaS User belongs to the customer-management side of the system.
- Website Members and Visitors belong to the website-audience side.
- Feature availability may depend on the customer's Plan.
- Plan and Subscription information can change over time.
- Website activity should be interpreted relative to the period in which a Website is live.
- Historical analysis must use the state that existed at the time being analyzed rather than only the current state.

These rules later influence:

- database constraints
- pipeline validation
- analytical populations
- SQL joins
- metric definitions

---

## 9. Events, States and Periods

A major modeling concept in the project is the difference between an **event** and a **state**.

An event represents something that happened at a specific point in time.

Examples:

```text
Payment completed
Feature used
Page viewed
Subscription changed
Support request opened
```

A state represents something that remains true over a period of time.

Examples:

```text
Website is live
Account is on a specific Plan
Feature is available
Subscription is active
```

These concepts require different representations.

```text
EVENT

---------●--------------------→ time
         ^
         something happened


STATE / PERIOD

---------|================|---→ time
      valid_from       valid_to
```

The project therefore uses historical periods where appropriate instead of relying only on current-state columns.

---

## 10. Why Historical Modeling Matters

Current state alone is not enough for many business questions.

Consider the question:

> Was this Account eligible to use a Feature when the activity occurred?

Using the Account's current Plan may produce the wrong answer.

Instead, the analysis needs the historical state:

```text
Event Timestamp
      ↓
Which Plan was active then?
      ↓
Was the Feature available under that Plan?
      ↓
Was the Account eligible?
```

The same principle applies to concepts such as:

- subscription state
- website live periods
- feature access
- customer commercial status

Historical modeling therefore supports both database correctness and analytical correctness.

---

## 11. Conceptual Model vs Logical Model

The project contains multiple modeling stages.

These should not be treated as interchangeable.

### Conceptual Model

The conceptual model answers questions such as:

- What exists in the business?
- Who owns what?
- Which actors interact?
- What relationships matter?
- Which states need history?

It is designed primarily for understanding the domain.

### Logical Relational Model

The logical model translates those concepts into a more detailed relational structure.

It includes:

- tables
- keys
- relationships
- constraints
- historical representations
- implementation-level business rules

The current documented logical model contains **49 relational tables**.

This does not mean that the earliest conceptual ERD contained 49 tables.

The conceptual ERD and the final relational model represent different stages of the design process.

---

## 12. Domain Documentation Groups

For documentation purposes, the model can be explored through several business-oriented groups.

### Customer & Account Domain

Focuses on:

- Accounts
- SaaS Users
- customer identity
- lifecycle context

### Product & Website Domain

Focuses on:

- Websites
- Pages
- Content
- website structure

### Visitor & Engagement Domain

Focuses on:

- Visitors
- Website Members
- Sessions
- Interaction Events
- Comments
- Ratings

### Subscription & Billing Domain

Focuses on:

- Plans
- Subscriptions
- Payments
- commercial lifecycle

### Feature & Entitlement Domain

Focuses on:

- Features
- plan availability
- eligibility
- enablement
- usage

### Support Domain

Focuses on:

- Support Requests
- customer service activity
- operational signals

These groups are documentation views of the larger model rather than separate databases.

A current visual ERD asset for this model is available in `assets/diagrams/saas_entity_relationship_diagram.png`.

---

## 13. From Business Questions to Data Requirements

The model was not designed independently from analytics.

Business questions helped determine which entities, relationships and historical states needed to exist.

The process can be summarized as:

```text
Business Question
       ↓
Required Population
       ↓
Required Entities
       ↓
Required Relationships
       ↓
Required Historical Context
       ↓
Data Requirements
       ↓
Source Datasets
       ↓
Database Model
```

For example, measuring feature adoption requires more than knowing that a Feature exists.

The system must also determine:

- which Accounts could access the Feature
- when they were eligible
- whether the Feature was enabled
- whether activity actually occurred

This is why business modeling, data modeling and analytical modeling are tightly connected in the project.

---

## 14. Model Evolution

The data model evolved iteratively as additional business and analytical requirements became clear.

```text
Business Concept
        ↓
Actors & Processes
        ↓
Conceptual Entities
        ↓
Relationships
        ↓
Lifecycle & Historical Modeling
        ↓
Data Requirements
        ↓
Dataset Design
        ↓
Logical Relational Model
        ↓
PostgreSQL Schema
```

The final model should therefore be understood as the result of several design stages rather than a schema created in a single step.

The evolution of these decisions is documented in the [Build Journey](../deep-dive/build_journey.md).

---

## 15. Related Documentation

### Continue the Core Story

- [Data Platform](02_data_platform.md)
- [Analytics](03_analytics.md)
- [Dashboard & Storytelling](04_dashboard_and_storytelling.md)
- [Reliability & Validation](05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](../deep-dive/engineering_decisions.md)
- [Build Journey](../deep-dive/build_journey.md)

### Reference

- [Glossary](../reference/glossary.md)
- [Schema Reference](../reference/schema_reference.md)
- [Data Lineage](../reference/data_lineage.md)

---

## Current Documentation Status

The business and conceptual structure is documented here.

The schema reference is already linked from this page, and a current ERD asset is available in `assets/diagrams/saas_entity_relationship_diagram.png`. Class diagrams are not part of the current published documentation set.
