# AI-Assisted Development

This project was developed using a **human-directed, strongly AI-assisted engineering workflow**.

AI was used extensively throughout the project.

Its role was especially significant in implementation-heavy areas such as:

- Python development
- SQL development
- data-pipeline architecture
- validation logic
- testing
- debugging
- analytical translation
- Power BI troubleshooting
- technical documentation

At the same time, the project was not developed through an autonomous "generate and accept" workflow.

The development process remained iterative:

```text
Business Need / Requirement
        ↓
Discussion & Reasoning
        ↓
Design Decision
        ↓
AI-Assisted Implementation
        ↓
Local Execution
        ↓
Observed Output / Error
        ↓
Review
        ↓
Correction
        ↓
Run Again
        ↓
Validated Result
```

This document explains that workflow transparently.

---

## 1. Why AI Was Used

The project covers several connected areas:

```text
Business Modeling
Data Modeling
Synthetic Data
PostgreSQL
Python Pipeline Engineering
Testing
Data Quality
SQL Analytics
Serving Views
Power BI
Documentation
```

Implementing every component manually from scratch would require substantial time.

AI was therefore used as an engineering accelerator.

The goal was to spend less time on repetitive implementation and more time on:

- defining requirements
- understanding concepts
- evaluating alternatives
- executing the system
- investigating failures
- validating behavior
- interpreting analytical results
- improving the overall architecture

---

## 2. The Development Model

The most accurate description of the workflow is:

> **Human-Directed, AI-Assisted Engineering**

This means that development was neither:

```text
Entirely Manual Development
```

nor:

```text
Autonomous AI Development
```

Instead, the process combined human direction with extensive AI implementation assistance.

---

## 3. Human Direction

Human involvement included areas such as:

- defining the fictional business environment
- deciding what the system should represent
- identifying important business entities
- discussing relationships and ownership
- determining which business questions mattered
- defining requirements
- evaluating proposed alternatives
- deciding how metrics should be interpreted
- running the implementation locally
- inspecting outputs
- identifying unexpected behavior
- reporting errors
- requesting corrections
- reviewing dashboard behavior
- interpreting analytical results
- deciding what belonged in the final portfolio

The development process therefore retained continuous human involvement.

---

## 4. AI Assistance

AI assistance included areas such as:

- proposing implementation structures
- generating Python code
- generating SQL
- helping design pipeline modules
- suggesting database patterns
- implementing validation logic
- generating tests
- generating Data Quality rules
- proposing reconciliation checks
- debugging errors
- explaining technical concepts
- exploring alternative implementations
- helping organize Power BI logic
- assisting with dashboard troubleshooting
- structuring technical documentation

AI contributed heavily to the technical implementation.

That contribution is intentionally documented rather than hidden.

---

## 5. No Artificial Authorship Percentage

The project does not attempt to claim that:

```text
X% was written by the developer
```

or:

```text
Y% was written by AI
```

Such percentages would be difficult to define meaningfully.

For example, a piece of SQL might involve:

```text
Human Business Question
        ↓
Joint Metric Definition
        ↓
AI-Generated Initial Query
        ↓
Human Local Execution
        ↓
Observed Incorrect Result
        ↓
Joint Debugging
        ↓
AI-Generated Correction
        ↓
Human Verification
```

Reducing this process to a simple authorship percentage would hide how the work was actually performed.

The repository therefore describes roles and workflow instead.

---

## 6. Business and Domain Modeling

AI was used early in the project as a reasoning and design partner.

The process included discussion of:

- SaaS business structure
- customer roles
- Website ownership
- visitors and members
- subscriptions
- plans
- features
- support
- historical state

The business model was refined through repeated discussion.

For example, distinctions such as:

```text
Account
≠
SaaS User
≠
Website Member
≠
Visitor
```

were important because they later affected both database design and analytical populations.

AI helped structure and challenge the model.

The final project direction remained tied to the intended business scenario and project goals.

---

## 7. Translating Business Concepts Into a Data Model

Once the business concepts were defined, AI assisted with translating them into more formal data structures.

This included support for:

- conceptual entities
- relationships
- cardinality
- historical modeling
- logical relational design
- keys
- constraints
- naming
- documentation

The workflow often looked like:

```text
Business Concept
      ↓
Discussion
      ↓
Proposed Data Structure
      ↓
Review
      ↓
Refinement
```

This was especially useful as the project grew beyond a small number of entities.

---

## 8. Synthetic Data Development

Because the business is fictional, the project required synthetic data.

AI assisted extensively with:

- dataset structure
- generation logic
- realistic relationships
- lifecycle consistency
- event generation
- historical states
- corrective scripts
- validation logic

The purpose was not simply to generate random rows.

The generated data needed to support:

```text
Business Rules
+
Referential Relationships
+
Historical Analysis
+
Pipeline Validation
+
Analytics
```

The data-generation process was therefore iterative.

Generated output was inspected, problems were identified, and logic was revised.

---

## 9. Python Pipeline Implementation

The Python data pipeline is one of the areas where AI assistance was strongest.

AI helped implement or structure concepts such as:

- configuration
- path handling
- metadata
- ingestion
- validation
- integrity checks
- transformation
- dependency-aware loading
- database access
- rerun semantics
- Data Quality
- logging
- run history

The development pattern was commonly:

```text
Requirement
      ↓
Explain Desired Behavior
      ↓
AI-Assisted Code
      ↓
Run in Local PyCharm Environment
      ↓
Observe Result
```

If the result was incorrect:

```text
Error / Unexpected Output
        ↓
Share Result
        ↓
Investigate
        ↓
Modify Implementation
        ↓
Run Again
```

This cycle occurred repeatedly during development.

---

## 10. Learning Through Pipeline Development

The project also served as a hands-on learning environment.

Before implementing some of the pipeline functionality, concepts such as:

- atomic loading
- rollback
- rerun semantics
- dependency-aware loading
- batch identity
- run identity
- duplicate delivery
- idempotent behavior

were not merely treated as existing knowledge.

They were explored while building the system.

The learning process often followed:

```text
New Concept
      ↓
Explanation
      ↓
Implementation
      ↓
Local Execution
      ↓
Observed Behavior
      ↓
Questions
      ↓
Refinement
```

The project therefore reflects both implementation and learning.

---

## 11. Local Execution Was Central

AI could generate implementation suggestions, but it did not execute the complete project inside the user's local environment.

The implementation was repeatedly run locally.

This mattered because actual execution exposed issues related to:

- PostgreSQL
- paths
- Python environment
- data files
- database state
- package behavior
- Power BI
- local configuration

The workflow therefore depended on real execution feedback.

```text
AI Suggestion
      ↓
Local Environment
      ↓
Actual Result
      ↓
Feedback
```

This prevented the project from becoming a collection of unexecuted generated code.

---

## 12. Debugging as a Collaborative Loop

Debugging was one of the strongest examples of the AI-assisted workflow.

A typical debugging cycle was:

```text
Run Code
   ↓
Error
   ↓
Inspect Error Message
   ↓
Provide Error / Screenshot / Output
   ↓
Reason About Cause
   ↓
Propose Fix
   ↓
Apply Fix
   ↓
Run Again
```

Sometimes the first correction was not enough.

The loop continued until the expected behavior was observed.

This means debugging involved both:

```text
AI reasoning
+
real local execution evidence
```

---

## 13. Testing

AI was heavily used to help create and expand software tests.

Assistance included:

- identifying behaviors worth testing
- generating pytest cases
- proposing edge cases
- building fixtures
- testing failures
- testing reruns
- testing rollback behavior
- testing duplicate handling
- testing command behavior

However, an AI-generated test was not treated as proof merely because it existed.

The relevant sequence was:

```text
Requirement
      ↓
Test
      ↓
Execute
      ↓
PASS / FAIL
      ↓
Interpret
```

The historical reference implementation contains **39 software tests**.

These tests are documented separately from Data Quality and serving checks.

---

## 14. Data Quality

AI also assisted extensively with Data Quality design and implementation.

This included:

- proposing rules
- translating business expectations into checks
- writing SQL or Python logic
- identifying cross-table consistency requirements
- debugging violations

The goal was not to generate the largest possible number of rules.

The goal was to check meaningful business and relational conditions.

The historical reference implementation contains **32 Data Quality rules**.

These belong to a different verification layer from software tests.

---

## 15. Duplicate and Conflict Logic

The event deduplication policy required explicit reasoning.

The project needed to distinguish:

```text
Same Event ID
+
Same Payload
        ↓
Duplicate Delivery
```

from:

```text
Same Event ID
+
Different Payload
        ↓
Conflict
```

AI assisted with turning this requirement into implementation logic.

The requirement itself was discussed and validated as a system behavior rather than accepted as an arbitrary generated solution.

---

## 16. Rerun Semantics

Rerun behavior followed a similar process.

The intended policy became:

```text
same batch_id
+
same fingerprint
        ↓
SKIP
```

and:

```text
same batch_id
+
different fingerprint
        ↓
STOP
```

AI helped implement and test this behavior.

Local execution was then used to verify that the pipeline behaved according to the intended contract.

---

## 17. SQL Development

SQL was another area where AI assistance was substantial.

AI helped with:

- joins
- aggregation
- window logic
- historical joins
- metric calculations
- validation queries
- analytical exploration
- serving views
- reconciliation

However, the analytical process did not begin with:

```text
"Write a query."
```

Instead, it generally followed:

```text
Business Question
      ↓
What should the metric mean?
      ↓
Population
      ↓
Grain
      ↓
Denominator
      ↓
Time Definition
      ↓
SQL Implementation
```

This distinction is important.

AI accelerated technical translation.

It did not eliminate the need to decide what should be calculated.

---

## 18. Joint Analytical Reasoning

The analytical questions were developed collaboratively through discussion.

Examples included:

- First Paid Conversion
- Paid Retention
- Product vs Paid Activity
- Feature Adoption
- Website Outcomes
- Commercial Transitions

For each major area, reasoning included questions such as:

```text
Who belongs in the population?

What does one row represent?

What is the denominator?

Which time boundary applies?

Which historical state matters?

What should be excluded?
```

AI helped propose and analyze alternatives.

The resulting definition was then translated into implementation.

---

## 19. Analytical Translation

A representative analytical workflow was:

```text
Business Question
        ↓
Joint Analytical Reasoning
        ↓
Metric Contract
        ↓
AI-Assisted SQL
        ↓
Local Execution
        ↓
Observed Result
        ↓
Plausibility Review
        ↓
Validation Query
        ↓
Correction if Needed
```

This workflow is more accurately described as AI-assisted analysis implementation than as simple query generation.

---

## 20. Interpreting Results

AI also assisted in discussing analytical outputs.

However, numerical output was not automatically accepted.

Results were examined for:

- plausibility
- population size
- unexpected patterns
- denominator issues
- time-window issues
- grain issues
- differences between alternative definitions

This occasionally led back to the metric definition itself.

```text
Unexpected Result
      ↓
Check SQL
      ↓
Check Population
      ↓
Check Time Definition
      ↓
Check Business Meaning
```

This feedback loop was an important part of the analytical work.

---

## 21. Power BI Development

AI assistance continued into Power BI.

The project involved repeated work around:

- report-page organization
- serving-view selection
- filter behavior
- visual aggregation
- percentages
- cards
- slicers
- snapshot metrics
- semantic-model structure

Because Power BI is visual and stateful, implementation could not be validated from generated text alone.

---

## 22. Screenshot-Based Dashboard Review

Dashboard development often followed:

```text
Implement in Power BI
      ↓
Open Report
      ↓
Inspect Visual
      ↓
Take Screenshot
      ↓
Discuss Result
      ↓
Identify Issue
      ↓
Apply Correction
      ↓
Inspect Again
```

This made visual feedback part of the development process.

AI could suggest a correction, but the final behavior had to be inspected in the actual application.

---

## 23. Business Storytelling

AI also helped structure the dashboard into a business narrative.

The three pages became:

```text
Customer Lifecycle & Multi-Dimensional Health

Website Audience Activity,
Engagement & Feedback

SaaS Product & Strategy Signals
```

The objective was not simply to arrange charts aesthetically.

The pages were organized around different families of business questions.

The dashboard therefore became a storytelling and decision-support layer.

---

## 24. Documentation

AI has played a major role in documentation.

The historical project contained:

- conversations
- intermediate files
- screenshots
- diagrams
- generated code
- query outputs
- multiple versions

AI was used to help:

- summarize the project
- identify important milestones
- organize architecture
- distinguish current from historical artifacts
- structure the GitHub portfolio
- draft technical documentation

The current repository documentation is therefore also part of the AI-assisted workflow.

---

## 25. Portfolio Architecture

AI assisted with the process of converting a large project history into a public repository.

The packaging process followed:

```text
Map Historical Project
        ↓
Identify Main Story
        ↓
Define Core Areas
        ↓
Define Deep Dives
        ↓
Create Repository Architecture
        ↓
Create Documentation
        ↓
Select Canonical Artifacts
```

The project was intentionally not published as a raw dump of development files.

---

## 26. What AI Did Not Replace

Despite substantial AI assistance, several activities still required human involvement.

AI did not replace the need to:

- decide the project goal
- choose what business problem to model
- determine what questions were important
- run local PostgreSQL
- execute pipeline commands
- inspect actual database outputs
- open Power BI
- inspect dashboard visuals
- provide screenshots
- identify whether a result looked wrong
- choose between competing business interpretations
- decide what should be published
- determine the final portfolio story

The project therefore remained interactive rather than autonomous.

---

## 27. Review Was Not Formal Code Review

It is important to describe review accurately.

The project involved substantial:

- reading
- discussion
- execution
- inspection
- debugging
- iterative correction

However, this should not automatically be described as formal professional code review for every generated line.

The repository therefore avoids exaggerated claims such as:

> Every line of AI-generated code was independently audited.

The more accurate statement is that implementation was repeatedly executed, inspected and iterated during development.

---

## 28. AI Assistance and Understanding

Using AI to accelerate implementation does not automatically imply understanding.

For that reason, a significant part of the development process involved asking:

```text
What does this do?

Why do we need it?

What happens if this fails?

Why is this approach different?

What does this output mean?
```

Concepts were discussed while the system was being built.

The project therefore functioned partly as a technical learning environment.

---

## 29. Example: Pipeline Reliability

A representative case study is pipeline reliability.

The process evolved approximately as:

```text
Need:
Reliable multi-table loading

        ↓

Discuss:
Dependencies
Transactions
Failures
Reruns

        ↓

AI-Assisted Implementation

        ↓

Run Locally

        ↓

Test Failure Conditions

        ↓

Observe Behavior

        ↓

Correct Implementation

        ↓

Lock Expected Semantics
```

The resulting behavior included concepts such as:

- validation-before-load
- rollback
- dependency-aware loading
- duplicate policies
- rerun semantics
- run history

---

## 30. Example: Analytical Metric

Another representative case study is Feature Adoption.

The workflow was not:

```text
Ask AI for feature-adoption SQL
```

Instead:

```text
Business Question
        ↓
What does adoption mean?
        ↓
Who had access?
        ↓
Historical Plan Context
        ↓
Eligible Population
        ↓
Usage Definition
        ↓
Metric Contract
        ↓
AI-Assisted SQL
        ↓
Run
        ↓
Review
```

This distinction is central to how analytical AI assistance was used.

---

## 31. Example: Dashboard Correction

Dashboard development provides another example.

```text
Expected Visual Behavior
        ↓
Implement
        ↓
Open in Power BI
        ↓
Observed Behavior Differs
        ↓
Screenshot / Description
        ↓
Reason About Filter or Aggregation
        ↓
Correction
        ↓
Refresh
        ↓
Visual Verification
```

This demonstrates why real execution remained necessary even when implementation guidance came from AI.

---

## 32. Benefits of the Workflow

The AI-assisted workflow provided several benefits.

### Faster Implementation

Large amounts of Python, SQL and documentation could be created more quickly.

### More Exploration

Alternative approaches could be considered without manually implementing every option first.

### More Verification Ideas

AI could propose additional:

- tests
- edge cases
- Data Quality checks
- reconciliation queries

### Faster Debugging

Errors and outputs could be analyzed interactively.

### Learning Support

Technical concepts could be explained at the point where they appeared in the project.

---

## 33. Risks of the Workflow

AI-assisted engineering also introduces risks.

Potential risks include:

- incorrect generated code
- plausible but wrong SQL
- hidden assumptions
- inconsistent naming
- outdated logic
- overcomplicated architecture
- tests that validate the wrong behavior
- documentation that overstates implementation

These risks influenced the project's validation strategy.

---

## 34. How Those Risks Were Managed

The project attempted to reduce those risks through:

```text
Explicit Requirements
        ↓
Local Execution
        ↓
Observed Results
        ↓
Validation
        ↓
Discussion
        ↓
Correction
```

Additional protection came from:

- database constraints
- Data Quality checks
- software tests
- reconciliation
- analytical contracts
- serving validation
- dashboard inspection

The objective was not to assume generated implementation was correct.

---

## 35. AI and Evidence

The repository distinguishes between:

```text
Generated Artifact
```

and:

```text
Validated Evidence
```

For example:

```text
AI Generates Test
        ↓
Test File Exists
```

is not equivalent to:

```text
Run Test Suite
        ↓
Observe PASS
        ↓
Compare With Expected Behavior
```

Similarly:

```text
AI Generates SQL
```

does not automatically prove:

```text
Analytical Metric Is Correct
```

The implementation must still match its analytical contract.

---

## 36. Why This Workflow Is Documented

AI usage is documented for three reasons.

### Transparency

It accurately represents how the project was built.

### Technical Relevance

AI-assisted development is itself becoming part of modern engineering workflows.

### Interpretation

Readers should understand that implementation speed was partly enabled by AI assistance while design, execution and validation remained iterative human activities.

---

## 37. What This Repository Does Not Claim

The project does not claim that:

```text
Every line was written manually.
```

It also does not claim that:

```text
AI autonomously designed and built the complete project.
```

It does not claim that:

```text
AI-generated output was always correct on the first attempt.
```

And it does not attempt to assign a precise percentage of authorship.

---

## 38. Current Working Principle

The working principle throughout the repository is:

> Use AI aggressively to accelerate implementation and exploration, while keeping requirements, execution, validation and interpretation explicit.

This can be represented as:

```text
Human Direction
       +
AI Acceleration
       +
Real Execution
       +
Validation
       =
AI-Assisted Engineering Workflow
```

---

## 39. Relationship to the Portfolio

The AI-assisted workflow is intentionally documented as part of the project rather than hidden in a footnote.

However, it is also not intended to dominate the portfolio.

The primary project story remains:

```text
Business Modeling
        ↓
Data Engineering
        ↓
Analytics
        ↓
Power BI
        ↓
Reliability
```

AI describes **how much of the work was accelerated and developed**, not the business problem the platform exists to solve.

---

## Related Documentation

### Core Story

- [Business & Data Model](../core/01_business_and_data_model.md)
- [Data Platform](../core/02_data_platform.md)
- [Analytics](../core/03_analytics.md)
- [Dashboard & Storytelling](../core/04_dashboard_and_storytelling.md)
- [Reliability & Validation](../core/05_reliability_and_validation.md)

### Deep Dive

- [Engineering Decisions](engineering_decisions.md)
- [Build Journey](build_journey.md)
- [Reproducibility](reproducibility.md)
- [Limitations & Future Roadmap](limitations_and_roadmap.md)

---

## Current Documentation Status

This document describes the development methodology used throughout the project.

Selected case studies may be added later to connect specific requirements, AI-assisted implementations, local execution results and final corrections to concrete repository artifacts.