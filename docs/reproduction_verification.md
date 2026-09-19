# Fresh-clone reproduction verification

Verification date: 2026-09-19

## Scope

This report records a local reproduction of the published SaaS Website
Builder data platform using a fresh Git clone, the verified frozen data
release, and a separate PostgreSQL database.

Historical source commit tested: `88f400e`.

The initial reproduction used the historical source commit. A subsequent
single-expression Serving SQL correction was verified separately.

## Environment and inputs

- PostgreSQL server and `psql`: 18.0.
- Python: 3.11.9.
- Frozen data release: `data-v1.0`.
- Release ZIP SHA256:
  `9d00f823b1c05a000a3c8837ceb56490d08e03d353489df3fb947405319036c5`.
- Source datasets: 49 (44 CSV and 5 JSONL).
- Separate reproduction database: `saas_website_builder_repro_v1`.
- Separate integration-test database: `saas_website_builder_repro_v1_test`.

The original development databases were not used as reproduction targets.

## Reproduction results

| Check | Observed result |
| --- | --- |
| Frozen source file availability | 49/49 |
| Source row-count checks | 49/49 |
| Source SHA256 checks | 49/49 |
| Raw records processed | 2,903,577 |
| Exact duplicate deliveries skipped | 3,638 |
| Rows loaded into PostgreSQL | 2,899,939 |
| Operational tables reconciled | 49/49 |
| Canonical batch outcome | SUCCESS |
| Full-load transaction | COMMIT |
| Data Quality rules | 32 PASS, 0 FAIL, 0 violations |
| Serving Views installed | 12/12 |
| Serving Views queried successfully | 12/12 |

The full load completed in 306.161 seconds in this local environment.
The Data Quality run completed in 179.125 seconds. These timings are
observations, not performance guarantees.

## Dashboard reference measurements

The reproduced Serving Views returned:

**First paid conversion** (cohort size: 490):
D30 9.39%, D60 14.29%, D90 16.94%, D180 17.35%.

**Paid retention** (cohort size: 143):
M1 95.80%, M3 87.41%, M6 79.72%, M12 66.43%.

**Commercial transitions**:
786 events involving 600 distinct accounts; 683 upgrades,
9 downgrades, 82 cancellations, and 12 reactivations.

These measurements matched the previously documented project reference
values. Additional lifecycle KPI values were inspected, but not every
field was independently compared against a reference result.

## Python environment and automated tests

A separate virtual environment was created outside both repositories.
The published `requirements.txt` and `requirements-dev.txt` installed
successfully, `pip check` reported no broken requirements, and the
pipeline CLI help command completed successfully.

Using this new virtual environment:

- Non-integration tests: 28 passed.
- Full pytest suite: 39 passed, including 11 integration tests.
- Integration fixtures ran against the separate `_test` database.
- Post-test checks found zero remaining batch and run-history records
  in the integration-test database.

The full data load and DQ run had already completed using the original
development virtual environment. They were not repeated from the
newly created virtual environment.

## Serving label correction

The historical SQL source contained one malformed arrow expression in
`dashboard.vw_commercial_transition.path_label`.

The corrected source uses PostgreSQL's Unicode escape expression
`U&' \2192 '::text` to produce the right-arrow character.

The correction was applied separately to the reproduction database using
`CREATE OR REPLACE VIEW`. All eight commercial transition paths were
checked, their labels were corrected, and their numeric metrics remained
unchanged. The transaction committed successfully.

The historical clone was intentionally left unchanged to preserve the
source used for the original reproduction.

## Boundaries

This is a verified local reproduction, not a claim of testing on a
completely new computer. PostgreSQL and the base Python interpreter
were already installed locally.

The Power BI report was not reconnected to the reproduced database or
refreshed as part of this verification. The 12 SQL Serving Views were
installed and queried directly.

A full-load rerun on the reproduced database was not performed. Rerun
behavior is covered by the automated test suite.

## Related files

- [Operational schema](../sql/10_schema/001_operational_schema.sql)
- [Pipeline metadata](../sql/20_operational_metadata/001_pipeline_metadata.sql)
- [Dashboard Serving Views](../sql/40_serving/001_dashboard_views.sql)
- [Data Quality rules](../sql/90_validation/001_data_quality_rules.sql)
