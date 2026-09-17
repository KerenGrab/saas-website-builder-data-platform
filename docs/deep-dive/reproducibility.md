# Reproducibility

This document describes the reproducibility strategy for the project.

Reproducibility is treated as a technical requirement rather than as a statement that the project "worked once."

The project distinguishes between several different reproducibility goals because they do not mean the same thing.

The central distinction is:

```text
Historical Successful Local Execution
                ≠
Verified Clean-Machine Reproduction
```

The project has historical evidence of successful local execution.

A full clean-machine reproduction will be verified as part of the public release process.

---

## 1. What Reproducibility Means in This Project

The project contains several layers:

```text
Synthetic Source Data
        ↓
PostgreSQL Schema
        ↓
Python Data Pipeline
        ↓
Validated Operational Database
        ↓
Analytical SQL
        ↓
Serving Layer
        ↓
Power BI
```

Reproducing the project therefore involves more than running one Python script.

A reproducible release needs enough information to reconstruct the intended path from source data to analytical output.

---

## 2. Two Different Reproducibility Goals

The project distinguishes between:

### A. Result Reproduction

Can another environment use the **verified frozen source package** and reproduce the documented database, analytical and serving results?

```text
Frozen Source Package
        ↓
Pipeline
        ↓
PostgreSQL
        ↓
Analytics
        ↓
Reference Results
```

This is the primary reproducibility target for the first public release.

### B. Exact Synthetic Data Regeneration

Can another environment run the synthetic-data generator and recreate the exact same complete source package from scratch?

```text
Generator
    ↓
Synthetic Data
    ↓
Exact Match to Frozen Reference Package
```

This is a separate and stronger claim.

The first public release does not need to claim exact regeneration unless that process is independently verified.

---

## 3. Why These Goals Are Separate

A project can be analytically reproducible from a frozen source dataset even when the exact synthetic generation process has not been proven to reproduce the same dataset byte-for-byte.

For example:

```text
Verified Dataset v1.0
        ↓
Same Pipeline
        ↓
Same Database State
        ↓
Same Analytical Results
```

can be reproducible even if:

```text
Run Generator Again
        ↓
Exact Same Source Files
```

has not yet been demonstrated.

Keeping these claims separate avoids overstating what has been verified.

---

## 4. Current Reproducibility Status

The current project has strong historical local execution evidence.

Historically verified areas include:

- source validation
- transformation
- dependency-aware loading
- PostgreSQL persistence
- duplicate handling
- rerun behavior
- rollback behavior
- Data Quality execution
- software tests
- analytical SQL
- serving validation
- Power BI inspection

However, the current GitHub repository is still being prepared as a clean public package.

Therefore:

```text
Historical Project Execution
        ↓
VERIFIED during development

Current Public Repository
        ↓
UNDER PREPARATION

Fresh Clean-Machine Reproduction
        ↓
TO BE VERIFIED before public release
```

---

## 5. Historical Success Is Evidence, Not Final Reproduction Proof

Historical logs, screenshots, test results and analytical outputs are useful evidence.

They show that the project components were executed successfully during development.

However:

```text
Worked on the original development machine
```

does not automatically prove:

```text
Works from a clean clone
on another environment
```

A clean reproduction may reveal missing assumptions such as:

- hidden local paths
- unlisted dependencies
- local database configuration
- missing SQL setup files
- environment variables
- Power BI local state
- undocumented manual steps

For this reason, the public release will explicitly include a fresh reproduction check.

---

## 6. Target Public Reproduction Flow

The intended public workflow is:

```text
Clone Repository
        ↓
Create Python Environment
        ↓
Install Dependencies
        ↓
Configure Environment Variables
        ↓
Create PostgreSQL Database
        ↓
Apply Database Setup / Schema
        ↓
Download Frozen Source Package
        ↓
Verify Dataset Checksum
        ↓
Run Pipeline
        ↓
Run Data Quality
        ↓
Run Software Tests
        ↓
Apply / Run Analytical SQL
        ↓
Build Serving Layer
        ↓
Compare Reference Results
        ↓
Open Power BI Project
```

The exact commands will be documented only after they are verified against the final canonical repository structure.

---

## 7. Repository vs Release Artifacts

Not every project artifact belongs directly in Git.

The publication strategy separates:

```text
Git Repository
        ↓
Code
SQL
Documentation
Contracts
Curated Samples
Diagrams
Power BI Project Source

GitHub Release
        ↓
Frozen Full Dataset
Checksum
Release Notes
Reference Package Metadata
```

This avoids putting large data files into normal Git history while still allowing another person to obtain the exact reference input.

---

## 8. Frozen Source Package

The project uses a frozen synthetic input package as the reference dataset.

The documented package contains:

```text
49 datasets
44 CSV files
5 JSONL files
```

The reference package contains approximately:

```text
2.9 million raw records
```

The exact release package will be published with version information and a checksum.

The checksum will allow users to verify:

> Is the downloaded package the same package used for the documented reference results?

---

## 9. Why the Full Dataset Is Not Stored Directly in Git

Some source files are too large for a clean normal Git workflow.

The complete frozen package is therefore intended to be distributed as a release artifact rather than committed directly into repository history.

The repository itself will contain:

```text
data/
│
├── contracts/
├── samples/
└── README.md
```

while the full data package is distributed separately.

This keeps the repository manageable while preserving reproducibility.

---

## 10. Dataset Integrity

Before using the frozen dataset, the reproduction workflow should verify its integrity.

Conceptually:

```text
Downloaded Dataset
        ↓
Calculate Checksum
        ↓
Compare With Published Checksum
        ↓
Match?
   ┌────┴────┐
  Yes        No
   ↓          ↓
Continue     STOP
```

This prevents an incomplete or modified dataset from being mistaken for the reference input.

---

## 11. Environment Configuration

Local configuration should not be committed into the repository.

The repository uses:

```text
.env.example
```

as the public configuration template.

A local environment may require values such as:

```text
DB_HOST
DB_PORT
DB_NAME
DB_USER
DB_PASSWORD
SOURCE_ROOT
```

Actual credentials remain local.

The intended pattern is:

```text
.env.example
      ↓
Copy locally
      ↓
.env
      ↓
Fill local values
```

The `.env` file is excluded from Git.

---

## 12. Database Reproduction

A reproducible database setup requires more than knowing that PostgreSQL was used.

The public repository should provide enough SQL to recreate the required database structure.

The intended SQL organization is:

```text
sql/
│
├── 00_setup/
├── 10_schema/
├── 20_operational_metadata/
├── 30_analytics/
├── 40_serving/
└── 90_validation/
```

The final reproduction guide will define the required execution order.

---

## 13. PostgreSQL Preconditions

The original development environment used local PostgreSQL.

The public documentation will need to specify:

- supported PostgreSQL version
- database creation requirements
- required extensions, if any
- encoding assumptions
- permissions
- schema setup order

These details should be verified rather than inferred from the historical development environment.

---

## 14. Python Environment

The repository contains:

```text
requirements.txt
requirements-dev.txt
```

These files currently act as placeholders until the canonical implementation is selected and the dependency set is verified.

Before the first public release, the project will determine:

```text
Runtime Dependencies
+
Development / Testing Dependencies
+
Compatible Python Version
```

The final files should allow another environment to install the dependencies required by the published code.

---

## 15. Why Dependency Versions Matter

A command such as:

```text
pip install pandas
```

does not guarantee that another environment receives the same behavior as the original environment.

Libraries evolve.

The release process should therefore determine which dependency versions need to be constrained.

The objective is to balance:

```text
Reproducibility
        ↕
Unnecessary Over-Pinning
```

The final dependency strategy will be documented after clean-environment testing.

---

## 16. Pipeline Reproduction

The canonical pipeline implementation has not yet been copied into the public repository.

Once selected, the expected workflow will be documented around commands such as:

```text
plan-check
transform-check
target-check
validate
dq
```

The exact public CLI and command syntax will only be documented after verification.

This avoids publishing instructions that reflect an older development version.

---

## 17. Reference Pipeline Behavior

The public reproduction should preserve important behavioral guarantees such as:

```text
Validation Before Load

Dependency-Aware Loading

Transactional Load

Rollback on Failure

Duplicate Handling

Rerun Semantics

Run History
```

Reproduction is therefore not only about achieving the same final row counts.

Important pipeline behavior should also remain consistent.

---

## 18. Reproducing Duplicate Handling

The reference source package contains documented identical duplicate deliveries.

Therefore:

```text
Raw Source Rows
        ↓
Known Identical Duplicate Delivery Handling
        ↓
Target Rows
```

The target database is not expected to contain every raw delivery as a separate business event.

The expected difference must be explained by the documented deduplication policy.

---

## 19. Reference Source-to-Target Counts

The historical reference package records:

```text
Raw source rows:
2,903,577

Identical duplicate deliveries:
3,638

Expected target rows after deduplication:
2,899,939
```

These values should eventually be connected to the exact evidence artifact used to validate the release.

They are reference expectations, not standalone proof of successful reproduction.

---

## 20. Data Quality Reproduction

The project contains a dedicated post-load Data Quality layer.

The historical reference implementation includes:

```text
32 Data Quality rules
```

A release reproduction should be able to execute the final canonical DQ implementation and compare its result with the reference evidence.

The intended outcome is not simply:

```text
script finished
```

but:

```text
expected rule set
+
expected result
+
evidence
```

---

## 21. Software Test Reproduction

The historical reference implementation includes:

```text
39 software tests
```

The public release should include the canonical test suite and documented test command.

A successful reproduction should confirm expected behavior around areas such as:

- validation
- loading
- reruns
- duplicate handling
- rollback
- run history

The exact test command will be documented after the canonical Python environment is verified.

---

## 22. Analytical Reproduction

Reproducing the operational database is not enough.

The project also needs to reproduce the analytical layer.

The intended path is:

```text
Operational Database
        ↓
Analytical SQL
        ↓
Expected Analytical Grain
        ↓
Metric Contract
        ↓
Reference Result
```

Important analytical results should eventually be linked to:

- SQL
- metric definition
- population
- time semantics
- reference evidence

This prevents a numerical result from being presented without the logic that produced it.

---

## 23. Serving-Layer Reproduction

The project includes serving outputs intended for Power BI.

The historical reference layer includes:

```text
12 serving views
```

and:

```text
38 serving checks
```

The final public release should verify the canonical serving definitions before these are treated as current release claims.

The reproduction process should confirm areas such as:

- expected views
- expected grain
- uniqueness
- output shape
- aggregation behavior
- analytical consistency

---

## 24. Power BI Reproduction

Power BI requires a slightly different reproduction strategy from Python and SQL.

The project intends to publish one verified Power BI Project source containing:

```text
Report
+
Semantic Model
```

The final reproduction process should verify that the project:

- opens successfully
- resolves its expected data connection configuration
- contains the intended three pages
- renders the expected visuals
- does not depend on unpublished local cache state

---

## 25. Power BI Local State Must Not Be Required

Files such as local cache and environment-specific state should not be part of the public reproduction contract.

The repository therefore excludes local artifacts such as:

```text
localSettings.json
cache.abf
unappliedChanges.json
```

where applicable.

The published Power BI source should contain the meaningful project definition rather than local temporary state.

---

## 26. Reference Results

The `evidence/` layer is intended to store selected reference outputs.

Conceptually:

```text
evidence/
│
├── reference-results/
│   ├── pipeline/
│   ├── schema/
│   ├── analytics/
│   └── serving/
│
└── release-validation/
```

These artifacts will help answer:

> Did the reproduction produce the expected result?

The repository does not need every historical log.

It needs enough curated evidence to validate important claims.

---

## 27. Claim → Evidence → Reproduction

The preferred documentation pattern is:

```text
Claim
   ↓
Evidence
   ↓
Reproduction Step
```

For example:

```text
Claim:
49 source datasets

Evidence:
Input contract

Reproduction:
Validate downloaded source package
```

or:

```text
Claim:
39 software tests

Evidence:
Reference test output

Reproduction:
Run canonical pytest command
```

This makes portfolio claims inspectable.

---

## 28. Clean-Machine Verification

Before the repository is made public, the intended final test is a clean-environment reproduction.

The objective is to simulate the experience of somebody who does not have the original development machine.

The verification should begin from:

```text
Fresh Repository Clone
+
Documented Prerequisites
+
Published Dataset
```

and should not rely on:

- existing local databases
- undocumented files
- IDE state
- old project directories
- hidden environment variables
- manually prepared tables
- cached Power BI data

---

## 29. Clean-Machine Validation Checklist

The final verification should cover the complete public workflow:

```text
Fresh Clone
    ↓
Environment Setup
    ↓
Dependency Installation
    ↓
Database Creation
    ↓
Schema Setup
    ↓
Dataset Download
    ↓
Checksum Verification
    ↓
Pipeline Execution
    ↓
DQ Execution
    ↓
Test Execution
    ↓
Analytics
    ↓
Serving
    ↓
Reference Comparison
    ↓
Power BI Verification
```

Failures during this process should lead to documentation or implementation corrections before public release.

---

## 30. Reproducibility Failure Is Useful Information

If a clean-machine test fails, that does not invalidate the historical project.

It reveals an undocumented dependency or assumption.

For example:

```text
Clean Run Fails
      ↓
Missing Requirement Found
      ↓
Repository / Documentation Updated
      ↓
Run Again
```

The clean reproduction test is therefore part of packaging the project professionally.

---

## 31. Security and Reproducibility

Reproducibility should not require publishing credentials.

The release must avoid files containing:

- database passwords
- authentication tokens
- user-specific IDE configuration
- local absolute paths
- private account information

Instead, public configuration should use templates such as:

```text
.env.example
```

with local values supplied by the person reproducing the project.

---

## 32. Local Paths

Historical development artifacts may contain paths tied to the original machine.

For example:

```text
C:\Users\<user>\...
```

These paths should not be part of the final reproduction contract.

The canonical code should use configurable or project-relative paths where appropriate.

This will be checked during canonical source cleanup.

---

## 33. Versioned Releases

Reproducibility should be tied to a specific project version.

The intended approach is:

```text
Repository Commit / Tag
        +
Release Dataset
        +
Checksum
        +
Release Notes
        +
Reference Evidence
```

For example:

```text
v1.0.0
```

should represent one documented combination of:

- code
- SQL
- data
- Power BI source
- reference results

This is stronger than saying:

> Use whatever is currently in the repository.

---

## 34. Reproducibility Scope for v1.0

The first public release is intended to focus on:

```text
Data Engineering
+
Analytics
+
Power BI
```

Machine Learning is not part of the current reproduction contract.

If ML is added later, it should become a separate extension with its own:

- data contract
- environment
- training workflow
- evaluation
- reproducibility requirements

---

## 35. What v1.0 Should Be Able to Demonstrate

A successful v1.0 reproduction should demonstrate the core chain:

```text
Verified Synthetic Input
        ↓
Reliable Data Pipeline
        ↓
PostgreSQL Operational Model
        ↓
Validated Database
        ↓
Analytical SQL
        ↓
Serving Layer
        ↓
Power BI Dashboard
```

This is the main technical story of the current project.

---

## 36. Current Gaps Before Reproducibility Can Be Locked

Several items still need to be finalized.

```text
Canonical Python Pipeline
Canonical Test Suite
Final SQL Setup
Canonical Analytical SQL
Canonical Serving SQL
Verified Dependency Versions
Frozen Release Dataset
Dataset Checksum
Final Power BI Project
Reference Evidence
Clean-Machine Test
```

These are publication tasks, not missing conceptual parts of the project.

---

## 37. Current Reproducibility Claim

At the current repository stage, the accurate statement is:

> The project has documented successful local development runs and validated reference results. The GitHub repository is currently being prepared for a clean, versioned reproduction workflow.

It would currently be inaccurate to claim:

> Clone this repository and the complete project is guaranteed to reproduce immediately.

That claim should only be made after the clean-machine release test is completed.

---

## 38. Reproducibility Target

The final target is:

```text
Clone
  ↓
Follow Documented Setup
  ↓
Use Verified Frozen Dataset
  ↓
Run Canonical Pipeline
  ↓
Create Validated Database
  ↓
Run Analytics & Serving
  ↓
Compare Reference Evidence
  ↓
Open Verified Power BI Project
```

with no dependency on undocumented historical project state.

---

## Related Documentation

### Core Story

- [Data Platform](../core/02_data_platform.md)
- [Analytics](../core/03_analytics.md)
- [Reliability & Validation](../core/05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](engineering_decisions.md)
- [Build Journey](build_journey.md)
- [AI-Assisted Development](ai_assisted_development.md)
- [Limitations & Future Roadmap](limitations_and_roadmap.md)

### Reference

- [Data Lineage](../reference/data_lineage.md)
- [Schema Reference](../reference/schema_reference.md)
- [Metric Reference](../reference/metric_reference.md)

### Repository Areas

- [Data](../../data/README.md)
- [SQL](../../sql/README.md)
- [Evidence](../../evidence/README.md)

---

## Current Documentation Status

The reproducibility strategy and current verification boundaries are documented here.

Exact installation commands, dependency versions, database setup instructions, dataset release links, pipeline commands and expected reference outputs will be added only after canonical artifact selection and clean-environment verification.