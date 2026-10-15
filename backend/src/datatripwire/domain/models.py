"""Domain models and data contracts for DataTripwire.

These models define data contracts for dataset profiling, mutation specifications,
pipeline business metrics, validation findings, mutation evaluations, rule recommendations,
and summary evaluation reports.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_serializer,
    field_validator,
    model_validator,
)

from datatripwire.domain.enums import (
    FindingSeverity,
    MutationType,
    RecommendationStatus,
    RuleType,
)


def _to_two_decimal_places(value: Any) -> Decimal:
    """Normalize input value to Decimal with exactly two decimal places."""
    if isinstance(value, Decimal):
        dec = value
    elif isinstance(value, (int, float, str)):
        dec = Decimal(str(value))
    else:
        raise TypeError(f"Cannot convert {type(value)} to Decimal currency")
    return dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class DatasetProfile(BaseModel):
    """Metadata profile of an ingested dataset.
    
    Contains structural metrics and schema metadata without storing
    raw tabular records inside the model.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    dataset_id: str = Field(..., min_length=1, description="Unique identifier for the dataset")
    filename: str = Field(..., min_length=1, description="Source filename or origin identifier")
    row_count: int = Field(..., ge=0, description="Total number of records in the dataset")
    column_count: int = Field(..., ge=0, description="Number of columns in the dataset")
    column_names: List[str] = Field(default_factory=list, description="Ordered list of column names")
    column_types: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of column name to inferred data type (e.g., string, integer, float)"
    )
    null_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of missing/null values per column"
    )
    duplicate_row_count: int = Field(
        default=0,
        ge=0,
        description="Number of duplicate records detected in the dataset"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the profile was generated"
    )
    null_percentages: Dict[str, float] = Field(
        default_factory=dict,
        description="Percentage of missing/null values per column"
    )
    numeric_summaries: Dict[str, Dict[str, float]] = Field(
        default_factory=dict,
        description="Basic numeric statistics (min, max, mean, sum) for numeric columns"
    )
    is_sales_compatible: bool = Field(
        default=False,
        description="True if dataset conforms to canonical sales schema"
    )
    is_manufacturing_compatible: bool = Field(
        default=False,
        description="True if dataset conforms to manufacturing industrial IoT schema"
    )
    detected_domain: str = Field(
        default="sales",
        description="Detected domain based on dataset columns (sales, manufacturing, general)"
    )
    domain_compatibility: Dict[str, bool] = Field(
        default_factory=dict,
        description="Compatibility status for each supported domain"
    )
    supported_domains: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed metadata for all supported domains"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Schema or profiling warnings"
    )

    @field_validator("dataset_id", "filename")
    @classmethod
    def validate_non_blank_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("String field cannot be empty or whitespace only")
        return v.strip()

    @model_validator(mode="after")
    def validate_null_counts_non_negative(self) -> DatasetProfile:
        for col, count in self.null_counts.items():
            if count < 0:
                raise ValueError(f"Null count for column '{col}' cannot be negative: {count}")
        return self


class MutationSpec(BaseModel):
    """Specification describing a requested synthetic data mutation."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    mutation_id: str = Field(..., min_length=1, description="Unique identifier for the mutation test")
    mutation_type: MutationType = Field(..., description="Category of mutation to execute")
    target_column: Optional[str] = Field(
        default=None,
        description="Target column name for column-specific mutations (e.g., unit_price, quantity)"
    )
    target_record_id: Optional[str] = Field(
        default=None,
        description="Identifier of a specific record to mutate or duplicate, if targeted"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tunable parameters for the mutation (e.g., factor, replacement_value, row_index)"
    )
    description: str = Field(..., min_length=1, description="Human-readable summary of the mutation")
    reproducibility_seed: Optional[int] = Field(
        default=None,
        description="Optional seed used for deterministic synthetic generation"
    )

    @field_validator("mutation_id", "description")
    @classmethod
    def validate_non_blank_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("String field cannot be empty or whitespace only")
        return v.strip()

    @field_validator("target_column", "target_record_id")
    @classmethod
    def validate_optional_non_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Target field cannot be whitespace only when provided")
        return v.strip() if v is not None else None

    @model_validator(mode="after")
    def validate_column_for_column_mutations(self) -> MutationSpec:
        # Require target_column for column-level value mutations
        if self.mutation_type in (MutationType.INVALID_QUANTITY, MutationType.INVALID_UNIT_PRICE):
            if not self.target_column:
                # Set reasonable default column if omitted
                default_col = "quantity" if self.mutation_type == MutationType.INVALID_QUANTITY else "unit_price"
                object.__setattr__(self, "target_column", default_col)
        elif self.mutation_type == MutationType.INVALID_SENSOR_VALUE and not self.target_column:
            object.__setattr__(self, "target_column", "vibration_mm_s")
        elif self.mutation_type == MutationType.MISSING_SENSOR_VALUE and not self.target_column:
            object.__setattr__(self, "target_column", "temperature_c")
        elif self.mutation_type == MutationType.INVALID_PRODUCTION_VALUE and not self.target_column:
            object.__setattr__(self, "target_column", "defect_count")
        return self


class PipelineMetrics(BaseModel):
    """Measurable business or operational outputs produced by the data pipeline.
    
    All monetary calculations maintain two decimal places precision using Decimal
    to avoid binary floating-point representation anomalies.
    """
    model_config = ConfigDict(frozen=True, extra="allow")

    domain: str = Field(default="sales", description="Domain profile of the metrics (sales, manufacturing, general)")

    # E-commerce sales business metrics
    total_revenue: Optional[Decimal] = Field(
        default=None,
        description="Sum of (quantity * unit_price) across transactions (sales domain)"
    )
    transaction_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total count of transactions processed (sales domain)"
    )
    customer_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count of distinct customers represented (sales domain)"
    )
    average_order_value: Optional[Decimal] = Field(
        default=None,
        description="Average revenue per transaction (revenue / transaction_count)"
    )

    # Manufacturing industrial IoT metrics
    total_readings: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total count of telemetry readings recorded"
    )
    unique_machines: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count of unique machine identifiers active in dataset"
    )
    unique_facilities: Optional[int] = Field(
        default=None,
        ge=0,
        description="Count of unique facility identifiers in dataset"
    )
    total_units_produced: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total production units manufactured"
    )
    total_defect_count: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total defect count recorded across all batches"
    )
    total_energy_kwh: Optional[float] = Field(
        default=None,
        description="Total energy consumption in kWh aggregated"
    )
    avg_temperature_c: Optional[float] = Field(
        default=None,
        description="Average machine temperature in Celsius"
    )
    max_temperature_c: Optional[float] = Field(
        default=None,
        description="Peak machine temperature in Celsius"
    )
    avg_vibration_mm_s: Optional[float] = Field(
        default=None,
        description="Average vibration in mm/s"
    )
    max_vibration_mm_s: Optional[float] = Field(
        default=None,
        description="Peak vibration in mm/s"
    )
    avg_pressure_bar: Optional[float] = Field(
        default=None,
        description="Average pressure in bar"
    )
    avg_motor_current_a: Optional[float] = Field(
        default=None,
        description="Average motor current in amperes"
    )
    avg_quality_pass_rate_pct: Optional[float] = Field(
        default=None,
        description="Average quality pass rate percentage (0-100%)"
    )

    manufacturing_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured key-value dictionary of all manufacturing metrics"
    )
    additional_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional supplementary business or operational indicators"
    )

    @field_validator("total_revenue", mode="before")
    @classmethod
    def parse_revenue(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        return _to_two_decimal_places(v)

    @field_validator("average_order_value", mode="before")
    @classmethod
    def parse_aov(cls, v: Any) -> Optional[Decimal]:
        if v is None:
            return None
        return _to_two_decimal_places(v)

    @field_serializer("total_revenue", "average_order_value", when_used="json")
    def serialize_decimal(self, v: Optional[Decimal]) -> Optional[str]:
        return str(v) if v is not None else None

    @model_validator(mode="after")
    def compute_aov_if_missing(self) -> PipelineMetrics:
        if (
            self.total_revenue is not None
            and self.average_order_value is None
            and self.transaction_count is not None
            and self.transaction_count > 0
        ):
            computed = (self.total_revenue / Decimal(self.transaction_count)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            object.__setattr__(self, "average_order_value", computed)
        return self


class ValidationFinding(BaseModel):
    """Result of an individual validation rule check on a dataset.
    
    Represents an observed discrepancy or confirmed rule adherence.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    finding_id: str = Field(..., min_length=1, description="Unique identifier for the finding")
    rule_id: str = Field(..., min_length=1, description="Identifier of the rule producing this finding")
    rule_type: RuleType = Field(..., description="Category of rule executed")
    severity: FindingSeverity = Field(..., description="Severity level of the finding")
    affected_column: Optional[str] = Field(default=None, description="Column affected by the violation")
    affected_record_ids: List[str] = Field(
        default_factory=list,
        description="List of primary record identifiers where the violation was detected"
    )
    explanation: str = Field(..., min_length=1, description="Human-readable explanation of the finding")
    detected: bool = Field(
        default=True,
        description="True if this finding represents an identified violation/fault"
    )

    @field_validator("finding_id", "rule_id", "explanation")
    @classmethod
    def validate_non_blank_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("String field cannot be empty or whitespace only")
        return v.strip()


class MutationEvaluation(BaseModel):
    """Evaluation result for a single injected synthetic mutation.
    
    Contrasts baseline pipeline metrics against mutated metrics and maps
    whether existing validation rules caught the fault or allowed it to escape.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    mutation_spec: MutationSpec = Field(..., description="The original mutation specification")
    applied: bool = Field(..., description="True if mutation was successfully injected into dataset copy")
    detected: Optional[bool] = Field(
        default=None,
        description="True if validation detected the fault, False if fault escaped, None if not applied"
    )
    findings: List[ValidationFinding] = Field(
        default_factory=list,
        description="Validation findings triggered during pipeline execution on the mutated data"
    )
    baseline_metrics: Optional[PipelineMetrics] = Field(
        default=None,
        description="Metrics produced by clean baseline dataset"
    )
    mutated_metrics: Optional[PipelineMetrics] = Field(
        default=None,
        description="Metrics produced after mutation injection"
    )
    metric_deltas: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Calculated downstream differences (e.g., revenue_delta, transaction_delta)"
    )
    failure_reason: Optional[str] = Field(
        default=None,
        description="Diagnostic explanation if mutation injection or evaluation could not complete"
    )
    evaluated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of evaluation run"
    )

    @model_validator(mode="after")
    def validate_detection_consistency(self) -> MutationEvaluation:
        # An unapplied mutation cannot be counted as detected
        if not self.applied and self.detected is True:
            raise ValueError("Unapplied mutation cannot be marked as detected")
        return self


class RuleRecommendation(BaseModel):
    """Actionable recommendation to improve data-pipeline validation coverage.
    
    Suggested when an injected mutation escapes the existing validation suite.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")

    recommendation_id: str = Field(..., min_length=1, description="Unique identifier for the recommendation")
    rule_type: RuleType = Field(..., description="Type of validation rule recommended")
    target_column: Optional[str] = Field(default=None, description="Column target for the proposed rule")
    description: str = Field(..., min_length=1, description="Concise rule summary")
    rationale: str = Field(..., min_length=1, description="Explanation of why this rule prevents escape")
    suggested_rule_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured parameter definition for configuring the rule"
    )
    code_snippet: Optional[str] = Field(
        default=None,
        description="Optional illustrative code snippet implementing the rule"
    )
    status: RecommendationStatus = Field(
        default=RecommendationStatus.SUGGESTED,
        description="Status of recommendation lifecycle"
    )

    @field_validator("recommendation_id", "description", "rationale")
    @classmethod
    def validate_non_blank_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("String field cannot be empty or whitespace only")
        return v.strip()


class EvaluationReport(BaseModel):
    """Comprehensive test report summarizing a batch of mutation evaluations.
    
    Includes aggregate counts, surviving mutants, rule recommendations, and
    calculates the mutation score.
    """
    model_config = ConfigDict(frozen=True, extra="ignore")

    report_id: str = Field(..., min_length=1, description="Unique report identifier")
    dataset_id: str = Field(..., min_length=1, description="Identifier of the dataset evaluated")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when report was generated"
    )
    total_attempted: int = Field(..., ge=0, description="Total mutations queued for evaluation")
    successfully_applied: int = Field(..., ge=0, description="Total mutations successfully injected")
    detected_mutations: int = Field(..., ge=0, description="Mutations detected by validation suite")
    surviving_mutations: int = Field(..., ge=0, description="Mutations that escaped validation undetected")
    failed_evaluations: int = Field(..., ge=0, description="Mutations that failed to apply or evaluate")
    evaluations: List[MutationEvaluation] = Field(
        default_factory=list,
        description="Itemized evaluations of each mutation"
    )
    recommendations: List[RuleRecommendation] = Field(
        default_factory=list,
        description="Proposed validation rules to catch surviving mutations"
    )
    baseline_metrics: Optional[PipelineMetrics] = Field(
        default=None,
        description="Clean baseline pipeline metrics"
    )
    summary_deltas: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Downstream business impact summary deltas"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context regarding pipeline version, environment, or ruleset"
    )

    @field_validator("report_id", "dataset_id")
    @classmethod
    def validate_non_blank_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("String field cannot be empty or whitespace only")
        return v.strip()

    @model_validator(mode="after")
    def validate_counts_consistency(self) -> EvaluationReport:
        # Detected + surviving cannot exceed successfully applied
        if self.detected_mutations + self.surviving_mutations > self.successfully_applied:
            raise ValueError(
                f"Sum of detected ({self.detected_mutations}) and surviving ({self.surviving_mutations}) "
                f"cannot exceed successfully applied ({self.successfully_applied})"
            )
        # Successfully applied + failed cannot exceed total attempted
        if self.successfully_applied + self.failed_evaluations > self.total_attempted:
            raise ValueError(
                f"Sum of successfully applied ({self.successfully_applied}) and failed "
                f"({self.failed_evaluations}) cannot exceed total attempted ({self.total_attempted})"
            )
        return self

    @computed_field
    @property
    def mutation_score(self) -> Optional[float]:
        """Calculate the mutation score as a percentage.
        
        Formula:
            (Detected eligible mutations / Total eligible applied mutations) * 100
            
        Returns:
            float score between 0.0 and 100.0, or None if no mutations were successfully applied.
            Never returns NaN, infinity, or a misleading 0.0 when denominator is zero.
        """
        if self.successfully_applied == 0:
            return None
        return round((self.detected_mutations / self.successfully_applied) * 100.0, 2)
