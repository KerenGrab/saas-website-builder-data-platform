# Analytics Results Validation

## Purpose

This document records reproducible analytical results verified directly against the canonical PostgreSQL database and dashboard serving layer.

Validation was performed against:

- Database: `saas_website_builder_9h`
- Schema: `dashboard`
- Validation date: 2026-09-19
- Source: canonical version-controlled serving views in `sql/40_serving/001_dashboard_views.sql`

These values were queried directly from PostgreSQL rather than copied from historical notes or dashboard screenshots.

---

## 1. First Paid Conversion

Source view:

`dashboard.vw_conversion_horizon`

Canonical definition:

- cohort begins after account activation
- first plan must be Free
- paid conversion is the first transition from Free to Standard or Premium
- a fixed comparable 180-day cohort is used
- cohort size: 490 accounts

| Horizon | Converted Accounts | Cohort Size | Conversion Rate |
|---|---:|---:|---:|
| D30 | 46 | 490 | 9.39% |
| D60 | 70 | 490 | 14.29% |
| D90 | 83 | 490 | 16.94% |
| D180 | 85 | 490 | 17.35% |

Result: PASS

---

## 2. Paid Retention

Source view:

`dashboard.vw_paid_retention_horizon`

Canonical paid-retention cohort size:

143 accounts

| Horizon | Retained Accounts | Cohort Size | Retention Rate |
|---|---:|---:|---:|
| M1 | 137 | 143 | 95.80% |
| M3 | 125 | 143 | 87.41% |
| M6 | 114 | 143 | 79.72% |
| M12 | 95 | 143 | 66.43% |

Result: PASS

---

## 3. Product vs Paid Alignment

Source view:

`dashboard.vw_product_paid_aligned`

This view compares product activity state with commercial paid state on an aligned cohort.

It is intentionally distinct from the canonical paid-retention metric above and should not replace `vw_paid_retention_horizon`.

| Horizon | Cohort | Product Active | Paid | Both | Product Only | Paid Only | Neither | Gross Mismatch | Gross Mismatch Rate | Net Gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| M1 | 143 | 49 | 140 | 49 | 0 | 91 | 3 | 91 | 63.64% | 63.64 pp |
| M3 | 143 | 86 | 132 | 86 | 0 | 46 | 11 | 46 | 32.17% | 32.17 pp |
| M6 | 143 | 88 | 114 | 83 | 5 | 31 | 24 | 36 | 25.17% | 18.18 pp |
| M12 | 143 | 84 | 97 | 75 | 9 | 22 | 37 | 31 | 21.68% | 9.09 pp |

At M12, 31 of 143 accounts are in mismatched product/commercial states, producing a gross mismatch rate of 21.68%.

Result: PASS

---

## 4. Eligibility-Aware Feature Adoption

Source view:

`dashboard.vw_feature_adoption`

The denominator is eligibility-aware: only Account x Feature pairs that were entitled to a feature are included.

| Feature | Eligible Pairs | Adopted Pairs | Adoption Rate |
|---|---:|---:|---:|
| basic_membership | 2,000 | 1,029 | 51.45% |
| basic_analytics | 2,000 | 996 | 49.80% |
| basic_forms | 2,000 | 968 | 48.40% |
| custom_domain_tools | 600 | 253 | 42.17% |
| site_search | 600 | 231 | 38.50% |
| advanced_forms | 600 | 185 | 30.83% |
| advanced_analytics | 137 | 33 | 24.09% |
| premium_video | 137 | 26 | 18.98% |

Overall:

- Eligible Account x Feature pairs: 8,074
- Adopted pairs: 3,721
- Overall eligibility-aware adoption rate: 46.09%

Result: PASS

---

## 5. Commercial Transitions

Source view:

`dashboard.vw_commercial_transition`

Overall:

- Transition events: 786
- Distinct accounts participating in transitions: 600

### Transition Types

| Transition Type | Events |
|---|---:|
| Upgrade | 683 |
| Downgrade | 9 |
| Cancel | 82 |
| Reactivate | 12 |
| **Total** | **786** |

### Transition Paths

| Type | Path | Events |
|---|---|---:|
| Upgrade | Free -> Standard | 550 |
| Upgrade | Standard -> Premium | 83 |
| Upgrade | Free -> Premium | 50 |
| Downgrade | Premium -> Standard | 9 |
| Cancel | Standard -> Free | 63 |
| Cancel | Premium -> Free | 19 |
| Reactivate | Free -> Standard | 8 |
| Reactivate | Free -> Premium | 4 |

The dominant path is Free -> Standard:

- 550 of 683 upgrades = 80.53%
- 550 of 786 total commercial transitions = 69.97%

Result: PASS

---

## 6. Website Audience and Outcome Metrics

Source view:

`dashboard.vw_website_monthly`

The serving layer explicitly identifies partial reporting periods through `is_partial_period`.

### Complete Months

Period:

2024-04-01 through 2025-12-01

| Metric | Value |
|---|---:|
| Sessions | 238,411 |
| Page Views | 569,442 |
| Pages per Session | 2.39 |
| Forms Submitted | 42,530 |
| Forms per 100 Sessions | 17.84 |
| Friction Events | 102,260 |
| Friction Events per 100 Sessions | 42.89 |
| Comments Posted | 17,404 |

### Partial Period

January 2026 is explicitly marked as a partial period.

| Metric | January 2026 |
|---|---:|
| Sessions | 1,589 |
| Page Views | 3,942 |
| Pages per Session | 2.48 |
| Forms Submitted | 289 |
| Forms per 100 Sessions | 18.19 |
| Friction Events | 680 |
| Friction Events per 100 Sessions | 42.79 |
| Comments Posted | 596 |

The partial period is kept separate when interpreting monthly trends.

For total-volume dashboard KPIs, complete and partial periods together produce:

- Sessions: 240,000
- Page Views: 573,384

Result: PASS

---

## 7. Rating Snapshot

Source view:

`dashboard.vw_rating_snapshot`

Overall rating metrics:

- Active ratings: 11,428
- Current average rating: 3.95
- Ratings of 4 or 5: 8,270
- Share of ratings that are 4 or 5: 72.37%

### Rating Distribution

| Rating | Active Ratings |
|---|---:|
| 1 | 558 |
| 2 | 890 |
| 3 | 1,710 |
| 4 | 3,650 |
| 5 | 4,620 |
| **Total** | **11,428** |

Result: PASS

---

## Validation Boundary

This evidence validates analytical outputs exposed through the canonical PostgreSQL dashboard serving layer.

It does not claim that the project contains seven physical analytical fact tables. The analytical model includes seven documented fact designs and five conformed dimensions, while the current reproducible PostgreSQL implementation exposes the verified analytical results through version-controlled serving views.

The dataset is synthetic and these metrics represent the behavior of the generated SaaS scenario, not production business performance.

---

## Final Result

PASS

The principal portfolio analytics have been independently re-queried from the canonical PostgreSQL database and match the documented dashboard results:

- First Paid Conversion
- Paid Retention
- Product vs Paid Alignment
- Eligibility-Aware Feature Adoption
- Commercial Transitions
- Website Audience and Outcomes
- Rating and Feedback Snapshot
