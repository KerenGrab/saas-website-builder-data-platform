# Operational Schema Validation

This document records static validation evidence for the canonical PostgreSQL operational schema used by the SaaS Website Builder Data Platform.

The purpose of this reference is to show what is actually defined in the version-controlled DDL rather than relying on historical notes or reconstructed documentation.

---

## 1. Canonical Schema Artifact

The validated schema artifact is:

```text
sql/10_schema/001_operational_schema.sql
```

SHA256:

```text
75BE6542A467322F7734618BA94D10456AAC6D5D43734B484ED4962C6B0F90AB
```

This hash identifies the exact DDL version used for the inventory below.

[View Canonical Operational Schema](../../../sql/10_schema/001_operational_schema.sql)

---

## 2. Schema Object Inventory

Direct inspection of the canonical DDL produced:

| Object Type | Count |
|---|---:|
| `CREATE TABLE` definitions | 49 |
| `PRIMARY KEY` clauses | 49 |
| `REFERENCES` clauses | 70 |
| `UNIQUE` clauses | 11 |
| `CHECK` clauses | 47 |
| Functions | 4 |
| Triggers | 6 |

Important interpretation:

```text
70 REFERENCES clauses
```

is reported as the number of foreign-key reference declarations found in the DDL.

It should not be interpreted as a count of separately named foreign-key constraints.

---

## 3. Operational Table Inventory

The canonical schema defines 49 operational tables.

### Account and Customer Lifecycle

```text
account
account_lifecycle_event
account_lifecycle_period
acquisition_source_attribution
saas_user
user_account_membership
user_account_membership_event
user_account_membership_period
user_account_role_assignment_period
signup_journey_context
signup_journey_event
```

### Website and Content

```text
website
website_address_period
website_lifecycle_event
website_live_period
page
page_access_period
content_item
content_item_access_period
```

### Audience and Sessions

```text
visitor
website_member
visitor_member_linkage
audience_session
session_lifecycle_event
session_member_attribution
session_traffic_attribution
audience_interaction_event
```

### Membership Behavior

```text
membership_invitation
invitation_outcome_event
member_registration_success_event
member_profile_update_event
member_state_period
membership_behaviour_event
```

### Product and Features

```text
feature
website_feature_enablement_period
feature_enablement_lifecycle_event
product_behaviour_event
plan_feature_entitlement_period
```

### Subscription and Billing

```text
plan_catalog
subscription_lifecycle_event
subscription_plan_period
billing_cycle_period
payment_refund_activity_event
```

### Feedback

```text
comment
comment_lifecycle_event
rating
rating_lifecycle_event
```

### Support

```text
support_request
support_lifecycle_event
```

The complete canonical inventory is therefore:

```text
49 tables
```

---

## 4. Primary-Key Coverage

The DDL contains:

```text
49 PRIMARY KEY clauses
```

across:

```text
49 CREATE TABLE definitions
```

This confirms that row identity is explicitly represented throughout the operational schema.

Primary-key design is part of the persisted relational contract rather than being inferred only by application code.

---

## 5. Referential Relationships

The DDL contains:

```text
70 REFERENCES clauses
```

These references encode relationships across the major business domains, including structures such as:

```text
Account
   ↓
Website
```

```text
Website
   ↓
Page
```

```text
Visitor
   ↓
Session
```

```text
Account
   ↓
Subscription History
```

```text
Plan
   ↓
Feature Entitlement
```

```text
Website
   ↓
Website Member
```

These relationships are also relevant to the dependency-aware pipeline load plan.

The pipeline cannot safely load relational data in arbitrary order when child records depend on existing parent state.

---

## 6. Uniqueness Rules

The canonical DDL contains:

```text
11 UNIQUE clauses
```

UNIQUE constraints protect model-level assumptions where duplicate values or duplicate combinations would represent invalid persisted state.

These constraints complement primary keys.

Conceptually:

```text
PRIMARY KEY
→ identifies a row

UNIQUE
→ protects additional uniqueness rules
```

---

## 7. Check Constraints

The DDL contains:

```text
47 CHECK clauses
```

CHECK constraints enforce permitted values and relational business conditions directly at the database layer.

This creates an additional protection boundary beyond pipeline validation:

```text
Source Validation
        ↓
Transformation
        ↓
PostgreSQL Constraints
```

The database therefore participates in protecting data correctness rather than acting only as passive storage.

---

## 8. Database Functions

The operational schema defines four PostgreSQL trigger functions.

### `public.enforce_contribution_same_website()`

```text
CREATE FUNCTION public.enforce_contribution_same_website()
RETURNS trigger
```

This function protects cross-entity consistency for contribution-style data such as comments and ratings.

Its associated triggers ensure that referenced entities remain within the same Website context.

---

### `public.enforce_refund_provenance()`

```text
CREATE FUNCTION public.enforce_refund_provenance()
RETURNS trigger
```

This function protects provenance rules around refund-related payment activity.

It provides a database-level guard for refund records rather than relying exclusively on upstream application logic.

---

### `public.guard_contribution_parent_website_change()`

```text
CREATE FUNCTION public.guard_contribution_parent_website_change()
RETURNS trigger
```

This function protects existing contribution relationships when parent entities are moved between Websites.

It prevents updates that could invalidate previously consistent relationships.

---

### `public.guard_refunded_payment_mutation()`

```text
CREATE FUNCTION public.guard_refunded_payment_mutation()
RETURNS trigger
```

This function protects refund-related payment history against mutations that would break previously established refund provenance.

---

## 9. Trigger Inventory

The canonical schema defines six triggers.

### Comment Website Consistency

```text
trg_comment_same_website
```

Attached to:

```text
public.comment
```

Execution:

```text
BEFORE INSERT
OR UPDATE OF member_id, page_id
```

Function:

```text
public.enforce_contribution_same_website()
```

---

### Website Member Parent-Move Guard

```text
trg_member_website_move_guard
```

Attached to:

```text
public.website_member
```

Execution:

```text
BEFORE UPDATE OF website_id
```

Function:

```text
public.guard_contribution_parent_website_change()
```

---

### Page Parent-Move Guard

```text
trg_page_website_move_guard
```

Attached to:

```text
public.page
```

Execution:

```text
BEFORE UPDATE OF website_id
```

Function:

```text
public.guard_contribution_parent_website_change()
```

---

### Rating Website Consistency

```text
trg_rating_same_website
```

Attached to:

```text
public.rating
```

Execution:

```text
BEFORE INSERT
OR UPDATE OF member_id, page_id
```

Function:

```text
public.enforce_contribution_same_website()
```

---

### Refund Provenance Guard

```text
trg_refund_provenance
```

Attached to:

```text
public.payment_refund_activity_event
```

Execution:

```text
BEFORE INSERT
OR UPDATE OF account_id,
             event_type,
             event_time,
             original_payment_ref
```

Function:

```text
public.enforce_refund_provenance()
```

---

### Refunded-Payment Mutation Guard

```text
trg_refunded_payment_mutation_guard
```

Attached to:

```text
public.payment_refund_activity_event
```

Execution:

```text
BEFORE UPDATE OF payment_ref,
                 account_id,
                 event_type,
                 event_time
```

Function:

```text
public.guard_refunded_payment_mutation()
```

---

## 10. Why Trigger-Level Protection Exists

Several integrity rules cannot be expressed safely through a simple single-column constraint.

For example:

```text
Comment
   ↓
Member

Comment
   ↓
Page
```

may each contain individually valid foreign keys while still referring to entities belonging to different Websites.

The trigger layer protects this kind of cross-row or cross-entity invariant.

Conceptually:

```text
Valid Foreign Keys
        ≠
Automatically Valid Business Relationship
```

The schema therefore combines:

```text
PK
+
FK / REFERENCES
+
UNIQUE
+
CHECK
+
Trigger-Based Guards
```

to protect persisted relational state.

---

## 11. Historical Modeling

The physical schema contains both event-style and period-style structures.

Examples of event tables include:

```text
account_lifecycle_event
audience_interaction_event
comment_lifecycle_event
feature_enablement_lifecycle_event
product_behaviour_event
rating_lifecycle_event
subscription_lifecycle_event
support_lifecycle_event
website_lifecycle_event
```

Examples of historical period tables include:

```text
account_lifecycle_period
billing_cycle_period
content_item_access_period
member_state_period
page_access_period
plan_feature_entitlement_period
subscription_plan_period
user_account_membership_period
user_account_role_assignment_period
website_address_period
website_feature_enablement_period
website_live_period
```

This distinction supports historical analysis based on the state that existed at the time being analyzed rather than only the current state.

---

## 12. Operational Schema and Pipeline

The physical schema directly influences pipeline execution.

```text
Relational Dependencies
        ↓
Dependency-Aware Load Plan
        ↓
Parent Data
        ↓
Child Data
```

The pipeline validates relationships before loading and then loads datasets according to the canonical dependency plan.

The behavior of this pipeline is documented in:

[Pipeline Behavior Validation](../pipeline/pipeline_behavior_validation.md)

---

## 13. Operational Schema and Analytics

The operational schema is not intended to be a one-to-one analytical star schema.

The project separates:

```text
Operational Relational Model
        ↓
Analytical Logic
        ↓
Serving Views
        ↓
Power BI
```

The operational schema preserves business records, identity, history, and relational integrity.

Downstream analytical logic reorganizes that information around business questions and reporting grains.

---

## 14. Validation Boundary

The inventory in this document is derived directly from static inspection of:

```text
sql/10_schema/001_operational_schema.sql
```

It verifies what the canonical DDL defines.

Separate end-to-end evidence verifies that the broader platform can reproduce the expected PostgreSQL business-data state using the canonical source package and pipeline.

See:

[End-to-End Reproduction Evidence](../../release-validation/end_to_end_reproduction.md)

---

## Verification Summary

| Verification | Result |
|---|---:|
| Canonical DDL identified | VERIFIED |
| DDL SHA256 captured | VERIFIED |
| Tables | 49 |
| PRIMARY KEY clauses | 49 |
| REFERENCES clauses | 70 |
| UNIQUE clauses | 11 |
| CHECK clauses | 47 |
| Functions | 4 |
| Triggers | 6 |
| Table inventory extracted from DDL | VERIFIED |
| Function inventory extracted from DDL | VERIFIED |
| Trigger inventory extracted from DDL | VERIFIED |

---

## Final Result

```text
Canonical Operational DDL      VERIFIED
DDL Identity / SHA256          VERIFIED
Table Inventory                49
Primary-Key Definitions        49
Foreign-Key References         70
UNIQUE Rules                   11
CHECK Rules                    47
Trigger Functions               4
Triggers                        6
Relational Integrity Layer     VERIFIED
```

The canonical PostgreSQL DDL defines a structured operational schema with explicit row identity, referential relationships, uniqueness rules, database-level checks, and trigger-based protections for invariants that require more than simple foreign-key validation.