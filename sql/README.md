# SQL

This directory contains the version-controlled PostgreSQL SQL layer for
the SaaS Website Builder Data Platform.

It separates operational schema definition, pipeline metadata,
analytical implementation, dashboard serving and Data Quality.

## Published SQL Inventory

| Area | File | Purpose |
|---|---|---|
| Operational schema | [10_schema/001_operational_schema.sql](10_schema/001_operational_schema.sql) | Canonical operational PostgreSQL tables, relationships, constraints and supporting database objects. |
| Pipeline metadata | [20_operational_metadata/001_pipeline_metadata.sql](20_operational_metadata/001_pipeline_metadata.sql) | Database metadata used by the canonical data pipeline. |
| Dashboard serving | [40_serving/001_dashboard_views.sql](40_serving/001_dashboard_views.sql) | Canonical dashboard-serving views consumed by Power BI. |
| Data Quality | [90_validation/001_data_quality_rules.sql](90_validation/001_data_quality_rules.sql) | Version-controlled Data Quality definitions. |

The repository contains four published SQL implementation files.

## Directory Structure

- `00_setup/` - reserved for database setup scripts; no standalone setup SQL is currently published here.
- `10_schema/` - operational PostgreSQL schema.
- `20_operational_metadata/` - pipeline metadata.
- `30_analytics/` - reserved for standalone analytical SQL; not yet populated with published queries.
- `40_serving/` - Power BI dashboard-serving views.
- `90_validation/` - Data Quality SQL.

The `.gitkeep` files preserve otherwise empty directory structure.

## Implementation Boundary

The operational schema and pipeline metadata are distinct from the
analytical model.

The project documents seven analytical fact designs and five shared
dimensions. These designs should not be interpreted as seven materialized
PostgreSQL fact tables.

The repository currently exposes its verified dashboard outputs through
the version-controlled serving SQL.

Standalone analytical queries are not yet published under
`sql/30_analytics/`.

The final release should either publish that SQL package or explicitly
retain and explain the current boundary.

## Database and Pipeline Order

The intended high-level dependency flow is:

1. Create and configure a PostgreSQL project database.
2. Establish the canonical operational schema and pipeline metadata.
3. Use the published frozen input package with the Python pipeline.
4. Validate and load the operational data.
5. Apply and verify the dashboard-serving definitions.
6. Verify Data Quality and analytical results against the reference evidence.
7. Configure and refresh the Power BI Project.

This is an architectural outline, not a verified copy-and-paste
fresh-clone installation script.

The exact executable setup order, prerequisites and commands still
require fresh-clone verification.

The Data Quality SQL is part of the documented validation layer.
Do not assume every SQL file should be executed manually in filename order;
follow the verified pipeline and release instructions.

## Frozen Data Release

The canonical 49-dataset input package is published separately from
normal Git history as
[data-v1.0](https://github.com/KerenGrab/saas-website-builder-data-platform/releases/tag/data-v1.0).

The package contains 44 CSV files and 5 JSONL files, representing
2,903,577 raw records.

See [Data](../data/README.md) for download instructions, the SHA256
checksum and the distinction between the frozen input and the generator.

## Dashboard Integration

The Power BI semantic model consumes the PostgreSQL `dashboard`
serving layer.

The canonical project source and the 12 dashboard view mappings are
documented in [Dashboard](../dashboard/README.md).

The serving SQL file is
[40_serving/001_dashboard_views.sql](40_serving/001_dashboard_views.sql).

## Validation and Evidence

See [Evidence](../evidence/README.md) for the recorded pipeline,
operational schema, serving and analytical validation results.

The clean-database end-to-end checkpoint and the still-unverified
fresh-clone workflow are different validation boundaries.

See [Reproducibility](../docs/deep-dive/reproducibility.md) for details.

## Related Documentation

- [Data Platform](../docs/core/02_data_platform.md)
- [Analytics](../docs/core/03_analytics.md)
- [Reliability & Validation](../docs/core/05_reliability_and_validation.md)
- [Schema Reference](../docs/reference/schema_reference.md)
- [Metric Reference](../docs/reference/metric_reference.md)
- [Data Lineage](../docs/reference/data_lineage.md)
