# Data

This directory documents the source-data layer used by the SaaS Website Builder Data Platform.

The complete frozen dataset is available as a downloadable GitHub Release rather than being stored directly in Git history.

This keeps the repository lightweight while preserving access to the full reproducible source package.

---

## Full Frozen Data Package

GitHub Release:

```text
Frozen Data Package v1.0
```

Release tag:

```text
data-v1.0
```

The release contains the complete source-data package used by the canonical pipeline.

### Package Contents

```text
49 source datasets
44 CSV files
5 JSONL files
2,903,577 raw records
```

The datasets are organized into four source families:

```text
Core Product
Event Tracking
Billing & Payment
Support
```

The release also contains the metadata required to validate and interpret the package:

```text
final_pipeline_input_contract.json
final_canonical_source_register.csv
final_correction_override_register.csv
FINAL_INPUT_CONTRACT_CLOSURE_REPORT.md
```

---

## Package Structure

After extraction, the package has the following structure:

```text
final_pipeline_input_package_v1_0/
├── final_pipeline_input_contract.json
├── final_canonical_source_register.csv
├── final_correction_override_register.csv
├── FINAL_INPUT_CONTRACT_CLOSURE_REPORT.md
└── raw/
    ├── billing_payment/
    ├── core_product/
    ├── event_tracking/
    └── support_ticketing/
```

The `raw/` directory contains all 49 canonical source datasets.

---

## Downloading the Full Dataset

The complete package can be downloaded from the GitHub Release:

```text
data-v1.0
```

Using GitHub CLI:

```powershell
gh release download data-v1.0 --pattern "final_pipeline_input_package_v1_0.zip"
```

The release also includes the corresponding checksum file:

```text
final_pipeline_input_package_v1_0.zip.sha256
```

---

## Release Package Size

The uncompressed source data is approximately:

```text
400.8 MB
```

The published compressed ZIP is approximately:

```text
35.98 MiB
```

Several event datasets are significantly larger than the rest of the package.

The largest source files include:

```text
38_audience_interaction_events.jsonl    ~220.27 MB
31_product_behaviour_events.jsonl        ~83.68 MB
34_session_lifecycle_events.jsonl        ~58.19 MB
42_membership_behaviour_events.jsonl      ~9.94 MB
33_audience_session.csv                    ~8.93 MB
```

For this reason, the complete raw dataset is distributed through GitHub Releases instead of being stored directly in normal Git history.

---

## ZIP Integrity

The published ZIP has the following SHA256 checksum:

```text
9d00f823b1c05a000a3c8837ceb56490d08e03d353489df3fb947405319036c5
```

The release also contains:

```text
final_pipeline_input_package_v1_0.zip.sha256
```

which can be used to verify the downloaded archive independently.

For example, on PowerShell:

```powershell
Get-FileHash .\final_pipeline_input_package_v1_0.zip -Algorithm SHA256
```

The resulting hash should match:

```text
9d00f823b1c05a000a3c8837ceb56490d08e03d353489df3fb947405319036c5
```

---

## Release Verification

The published ZIP was not only created and uploaded.

Before publication, it was:

```text
Created
    ↓
SHA256 calculated
    ↓
Extracted into a separate verification directory
    ↓
Loaded through the canonical pipeline
    ↓
All source files structurally validated
    ↓
Reference row counts verified
    ↓
Individual source SHA256 hashes verified
```

The final verification result was:

```text
Datasets structurally validated: 49/49
Total records scanned: 2,903,577
Frozen reference rows expected: 2,903,577
Reference row counts verified: 49/49
SHA256 hashes verified: 49/49
Full structural scan: OK
Frozen input integrity: OK
```

This confirms that the published release package matches the frozen source-data contract used by the project.

---

## Data Contracts

The lightweight canonical metadata is stored directly in the repository under:

```text
data/contracts/
```

Current contents:

```text
data/contracts/
├── final_pipeline_input_contract.json
├── final_canonical_source_register.csv
├── final_correction_override_register.csv
└── FINAL_INPUT_CONTRACT_CLOSURE_REPORT.md
```

These files remain version-controlled because they define the expected structure and integrity of the full source package.

---

## Canonical Input Contract

The main machine-readable contract is:

```text
final_pipeline_input_contract.json
```

The canonical pipeline reads this file to determine the expected source datasets and their metadata.

The verified contract reports:

```text
Contract version: 1.0
Status: FROZEN
Dataset count: 49
```

The pipeline also verified that:

```text
Canonical source files found: 49/49
```

---

## Source Families

### Core Product

Contains product and business-entity data such as:

```text
Accounts
SaaS Users
Memberships
Websites
Pages
Content Items
Features
Website Members
Comments
Ratings
```

These datasets mainly represent structured business entities, history and lifecycle state.

---

### Event Tracking

Contains high-volume behavioral and event-oriented datasets such as:

```text
Product Behaviour Events
Audience Sessions
Session Lifecycle Events
Audience Interaction Events
Signup Journey Events
Membership Behaviour Events
```

This family contains the largest datasets in the source package.

---

### Billing & Payment

Contains commercial and subscription-related data such as:

```text
Plan Catalog
Subscription Plan Periods
Billing Cycle Periods
Subscription Lifecycle Events
Payment / Refund Activity Events
```

These sources support conversion, retention, churn and commercial-transition analytics.

---

### Support

Contains customer-support activity such as:

```text
Support Requests
Support Lifecycle Events
```

Support data is used as an additional contextual signal in analytical work.

---

## Using the Package with the Pipeline

After downloading and extracting the release package, configure:

```text
SOURCE_ROOT
```

to point to the extracted package root.

For example:

```text
SOURCE_ROOT
│
├── final_pipeline_input_contract.json
├── final_canonical_source_register.csv
├── final_correction_override_register.csv
├── FINAL_INPUT_CONTRACT_CLOSURE_REPORT.md
└── raw/
```

The Python pipeline resolves the relevant paths through:

```text
pipeline/paths.py
```

Conceptually:

```text
SOURCE_ROOT
    ↓
final_pipeline_input_contract.json
    ↓
49 declared datasets
    ↓
raw/
    ↓
Canonical Pipeline
```

---

## Why Full Raw Data Is Not Stored in the Repository

The decision to distribute the full dataset separately is intentional.

The source package includes approximately:

```text
400.8 MB
```

of uncompressed data, including one individual event file larger than:

```text
220 MB
```

Keeping these files directly inside normal Git history would make the repository substantially heavier and would mix large generated data artifacts with source code and documentation.

The project therefore separates:

```text
Repository
    ↓
Code
Tests
SQL
Documentation
Contracts
Evidence

GitHub Release
    ↓
Complete frozen source-data package
```

This preserves both:

```text
Repository usability
+
Full dataset availability
```

---

## Data Reproducibility

The source package is frozen rather than dynamically regenerated during normal pipeline execution.

This means the project can refer to a stable input package with known:

```text
Dataset inventory
Row counts
File hashes
Contract version
```

That provides a consistent reference point for:

```text
Pipeline validation
Database loading
Data-quality checks
Analytical verification
Dashboard reproduction
```

---

## Synthetic Data

All data in this package is synthetic.

The project models a fictional Website Builder SaaS platform.

The source datasets were created specifically for this portfolio project and do not represent real customers, users, payments or production activity.

No real customer or production data is included.

---

## Samples

The repository does not currently publish artificial five-row versions of every source dataset.

The complete 49-dataset package is already available through the `data-v1.0` release, so users who want to inspect or reproduce the data layer can work with the actual frozen source package.

The `data/samples/` directory is reserved for selected explanatory examples only if they provide additional documentation value later.

---

## Related Documentation

For the broader project context, see:

```text
docs/core/01_business_and_data_model.md
docs/core/02_data_platform.md
docs/core/03_analytics.md
docs/core/05_reliability_and_validation.md

docs/reference/schema_reference.md
docs/reference/metric_reference.md
docs/reference/data_lineage.md
```

For the pipeline implementation, see:

```text
run_pipeline.py
pipeline/
tests/
pytest.ini
```

---

## Current Status

```text
Canonical input contract          VERIFIED
Canonical source inventory        VERIFIED
49 source files                   VERIFIED
2,903,577 raw records             VERIFIED
Source-level SHA256 checks        VERIFIED
Release ZIP                       VERIFIED
Release checksum                  PUBLISHED
Full frozen data package          AVAILABLE
```

The complete frozen source package is published under:

```text
data-v1.0
```