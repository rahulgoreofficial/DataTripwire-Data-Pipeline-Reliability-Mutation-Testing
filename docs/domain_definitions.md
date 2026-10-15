# DataTripwire: Domain Definitions and Data Contracts

This document formalizes the terminology, entity definitions, mathematical evaluation formulas, and validation conventions employed across DataTripwire.

---

## 1. Core Domain Entities

### `DatasetProfile`
Encapsulates structural metadata and profiling indicators for a dataset without loading full raw records into memory:
- **`dataset_id`**: Non-empty unique identifier string (e.g., `DS-SALES-01`).
- **`filename`**: Source filename or upload descriptor.
- **`row_count`**: Total record count ($\ge 0$).
- **`column_count`**: Total column count ($\ge 0$).
- **`column_names`**: Ordered sequence of column names.
- **`column_types`**: Inferred high-level data types (`string`, `integer`, `float`, `date`).
- **`null_counts`**: Per-column tally of missing values.
- **`duplicate_row_count`**: Number of duplicate rows detected in the raw input.
- **`created_at`**: UTC timestamp of profile creation.

### `MutationSpec`
Formal specification of an injected synthetic data fault:
- **`mutation_id`**: Unique mutation identifier (e.g., `MUT-101`).
- **`mutation_type`**: Enumeration value (`duplicate_row`, `missing_required_value`, `invalid_quantity`, `invalid_unit_price`, `dropped_row`).
- **`target_column`**: Column to which the mutation applies (e.g., `quantity`, `unit_price`).
- **`target_record_id`**: Primary identifier of a specific targeted row, if targeted.
- **`params`**: Key-value dictionary of tuning parameters (e.g., multiplier, injected value).
- **`description`**: Human-readable explanation of the test condition.
- **`reproducibility_seed`**: Optional integer seed for deterministic random generation.

### `PipelineMetrics`
Measurable business aggregations produced by running the data pipeline over a dataset:
- **`total_revenue`**: Sum of $(\text{quantity} \times \text{unit\_price})$ represented as a high-precision `Decimal` with two decimal places.
- **`transaction_count`**: Total count of processed transaction records ($\ge 0$).
- **`customer_count`**: Distinct count of unique customer IDs ($\ge 0$).
- **`average_order_value`**: Derived average order value ($\frac{\text{total\_revenue}}{\text{transaction\_count}}$) quantized to two decimal places.
- **`additional_metrics`**: Arbitrary supplementary indicators.

### `ValidationFinding`
An individual diagnostic emitted by the data-quality rules engine:
- **`finding_id`**: Unique finding identifier.
- **`rule_id`**: Identifier of the rule that produced this finding (e.g., `RULE-UNIQUE-TXN`).
- **`rule_type`**: Category of rule (`uniqueness`, `not_null`, `value_range`, `data_type`, `date_validity`).
- **`severity`**: Diagnostic level (`info`, `warning`, `error`, `critical`).
- **`affected_column`**: Associated column, if applicable.
- **`affected_record_ids`**: List of primary keys identifying the violating records.
- **`explanation`**: Human-readable narrative detailing the violation.
- **`detected`**: Boolean flag indicating if this finding constitutes a detected failure.

### `MutationEvaluation`
Outcome of evaluating a single injected mutation:
- **`mutation_spec`**: The originating `MutationSpec`.
- **`applied`**: Whether the mutation successfully altered the dataset copy.
- **`detected`**: `True` if validation flagged the fault, `False` if the fault escaped, or `None` if unapplied.
- **`findings`**: Collection of `ValidationFinding` records generated during evaluation.
- **`baseline_metrics`**: Clean baseline `PipelineMetrics`.
- **`mutated_metrics`**: Corrupted `PipelineMetrics` post-mutation.
- **`metric_deltas`**: Downstream variance dictionary (e.g., `revenue_delta`, `transaction_delta`).
- **`failure_reason`**: Diagnostic message if injection failed.

### `RuleRecommendation`
Structured recommendation generated when a mutation escapes existing validation:
- **`recommendation_id`**: Unique recommendation identifier.
- **`rule_type`**: Type of rule required to catch the escaping fault.
- **`target_column`**: Target column for rule application.
- **`description`**: Summary of the proposed rule.
- **`rationale`**: Business and technical rationale explaining how this rule prevents silent corruption.
- **`suggested_rule_config`**: Structured parameter dictionary for configuring the rule.
- **`code_snippet`**: Optional illustrative code snippet.
- **`status`**: Lifecycle state (`suggested`, `applied`, `dismissed`).

### `EvaluationReport`
Summary report across a batch of mutation evaluations:
- **`report_id`**: Report identifier.
- **`dataset_id`**: Target dataset identifier.
- **`total_attempted`**: Total mutations queued.
- **`successfully_applied`**: Total mutations successfully injected into data copies.
- **`detected_mutations`**: Mutations successfully caught by active rules.
- **`surviving_mutations`**: Mutations that escaped detection undetected.
- **`failed_evaluations`**: Mutations that failed to apply or execute.
- **`mutation_score`**: Calculated percentage metric (or `None`).

---

## 2. Mathematical Evaluation Concepts

### Mutation Score Calculation
The mutation score measures the percentage of injected faults that existing validation rules detect:

$$\text{Mutation Score} = \left( \frac{\text{Detected Eligible Mutations}}{\text{Successfully Applied Eligible Mutations}} \right) \times 100$$

### Edge Case Handling
1. **Zero Denominator**: When `successfully_applied == 0`, the mutation score returns `None` (unavailable). It **never** returns `NaN`, `inf`, or `0.0%`, which would be mathematically false and misleading to stakeholders.
2. **Failed Injections**: If a mutation cannot be applied (e.g., target record does not exist), it is counted under `failed_evaluations`. It is **excluded** from both the numerator and the denominator of the score.
3. **Honest Detection**: An unapplied mutation cannot be marked as detected.

---

## 3. Supported Mutation Types

| Mutation Type | Description | Target Column | Downstream Business Risk |
| :--- | :--- | :--- | :--- |
| `duplicate_row` | Duplicates an existing transaction row | `transaction_id` | Silent inflation of revenue and order counts. |
| `missing_required_value` | Replaces a valid cell with `NaN` / null | Any mandatory column | Dropped records, broken aggregations, or runtime crashes. |
| `invalid_quantity` | Injects zero or negative quantity | `quantity` | Distorted inventory records, negative order volumes. |
| `invalid_unit_price` | Injects negative unit price | `unit_price` | Misleading revenue reduction or negative sales figures. |
| `dropped_row` | Deletes an entire record | N/A | Under-reported revenue and transaction volume. |

---

## 4. Sales Dataset Schema & Validation Conventions

### Column Schema
1. **`transaction_id`**: String primary identifier (e.g., `ORD-101`). Unique in clean data.
2. **`customer_id`**: String customer identifier (e.g., `CUST-201`). Can naturally repeat.
3. **`quantity`**: Integer quantity of items ordered ($> 0$).
4. **`unit_price`**: Non-negative monetary value ($\ge 0.00$).
5. **`transaction_date`**: ISO-8601 date string (`YYYY-MM-DD`).

### Baseline Rules vs. Configurable Uniqueness
- **Mandatory Baseline Rules**:
  - Null check across all columns.
  - Value range check: `quantity > 0`.
  - Value range check: `unit_price >= 0.00`.
  - Date format check: `YYYY-MM-DD`.
- **Configurable Uniqueness Rule**:
  - The uniqueness check on `transaction_id` is intentionally **disabled in the baseline suite**.
  - This allows the demonstration duplicate fault (`ORD-102`) to escape detection.
  - Upon escape, the recommendation engine suggests enabling the uniqueness rule, which subsequent re-testing verifies will catch the duplicate.

---

## 5. Monetary Conventions
- All monetary values are handled using Python's standard `Decimal` class.
- Precision is locked to two decimal places (`Decimal('0.01')`) using `ROUND_HALF_UP`.
- JSON serialization formats Decimals as strings (e.g., `"19000.00"`) to prevent floating-point conversion loss in JavaScript clients.
