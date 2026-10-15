"""API request and response schemas for DataTripwire.

These schemas define the wire format for dataset uploads, evaluations,
rule configurations, and health checks.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from datatripwire.domain.enums import MutationType
from datatripwire.domain.models import DatasetProfile


class ValidationRuleConfig(BaseModel):
    """Configuration toggles for the data-pipeline validation suite.
    
    Supports both e-commerce sales and manufacturing industrial IoT validation rules.
    Uniqueness rules are intentionally disabled by default in baseline suites to demonstrate fault survival.
    """
    model_config = ConfigDict(extra="allow")

    # E-commerce sales validation safeguards
    check_required_columns: bool = Field(default=True, description="Verify required columns are present")
    check_required_values: bool = Field(default=True, description="Verify required columns contain no null or NaN values")
    check_quantity_positive: bool = Field(default=True, description="Verify quantity is strictly greater than 0")
    check_unit_price_nonnegative: bool = Field(default=True, description="Verify unit price is non-negative (>= 0)")
    check_valid_transaction_date: bool = Field(default=True, description="Verify transaction_date conforms to ISO-8601 (YYYY-MM-DD)")
    check_unique_transaction_id: bool = Field(
        default=False,
        description="Verify transaction_id is completely unique. Intentionally False in baseline suite."
    )
    check_expected_row_count: bool = Field(
        default=False,
        description="Verify actual row count matches an expected reference count."
    )
    expected_row_count: Optional[int] = Field(
        default=None,
        description="Reference count used when check_expected_row_count is enabled"
    )

    # Manufacturing industrial IoT validation safeguards
    check_reading_id_unique: bool = Field(
        default=False,
        description="Verify reading_id is unique across all sensor records. Intentionally False in baseline suite."
    )
    check_machine_timestamp_unique: bool = Field(
        default=False,
        description="Verify composite (machine_id, timestamp) is unique. Key demo safeguard."
    )
    check_timestamp_validity: bool = Field(
        default=True,
        description="Verify timestamp values conform to valid date/time format"
    )
    check_sensor_numeric: bool = Field(
        default=True,
        description="Verify sensor measurements are numeric and finite"
    )
    check_non_negative_measurements: bool = Field(
        default=True,
        description="Verify pressure, vibration, motor current, power, energy, units, defects are non-negative"
    )
    check_quality_pass_rate_bounds: bool = Field(
        default=True,
        description="Verify quality pass rate percentage is between 0.0 and 100.0%"
    )
    check_production_consistency: bool = Field(
        default=True,
        description="Verify defect_count <= units_produced"
    )
    check_temperature_bounds: bool = Field(
        default=True,
        description="Verify temperature is within configured operating limits"
    )
    temperature_min_c: float = Field(
        default=40.0,
        description="Minimum operating temperature threshold in Celsius"
    )
    temperature_max_c: float = Field(
        default=95.0,
        description="Maximum operating temperature threshold in Celsius"
    )
    check_expected_record_count: bool = Field(
        default=False,
        description="Verify stream reading count matches expected reference count"
    )
    expected_record_count: Optional[int] = Field(
        default=None,
        description="Reference record count for manufacturing stream"
    )


class MutationRequestItem(BaseModel):
    """Specification of an individual requested mutation in an evaluation batch."""
    model_config = ConfigDict(extra="allow")

    mutation_type: MutationType = Field(..., description="Category of mutation to inject")
    target_transaction_id: Optional[str] = Field(
        default=None,
        description="Target transaction ID for sales mutations (e.g., ORD-102)"
    )
    target_record_id: Optional[str] = Field(
        default=None,
        description="Target identifier for record mutations (e.g. RDG-01-0001 or ORD-102)"
    )
    target_column: Optional[str] = Field(
        default=None,
        description="Target column name for column mutations (e.g., quantity, temperature_c)"
    )
    value: Optional[Any] = Field(
        default=None,
        description="Custom injected value (e.g., -100 for price, -2.5 for vibration, 150 for temperature)"
    )
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional additional tuning parameters"
    )
    description: Optional[str] = Field(
        default=None,
        description="Optional human-readable description for the test"
    )
    reproducibility_seed: Optional[int] = Field(
        default=None,
        description="Optional seed for deterministic generation"
    )

    @field_validator("mutation_type", mode="before")
    @classmethod
    def normalize_mutation_type(cls, v: Any) -> Any:
        if isinstance(v, str):
            val_clean = v.strip().lower()
            alias_map = {
                "drop_row": MutationType.DROPPED_ROW,
                "dropped_row": MutationType.DROPPED_ROW,
                "duplicate_reading": MutationType.DUPLICATE_SENSOR_READING,
                "duplicate_sensor": MutationType.DUPLICATE_SENSOR_READING,
                "missing_sensor": MutationType.MISSING_SENSOR_VALUE,
                "invalid_sensor": MutationType.INVALID_SENSOR_VALUE,
                "dropped_reading": MutationType.DROPPED_SENSOR_READING,
                "invalid_production": MutationType.INVALID_PRODUCTION_VALUE,
            }
            if val_clean in alias_map:
                return alias_map[val_clean]
            return MutationType(val_clean)
        return v


class EvaluationCreateRequest(BaseModel):
    """Request payload to initiate a mutation evaluation batch against a dataset."""
    model_config = ConfigDict(extra="allow")

    domain: Optional[str] = Field(
        default=None,
        description="Target domain profile ('sales', 'manufacturing', or auto-detect if None)"
    )
    mutations: List[MutationRequestItem] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="List of 1 to 10 mutations to evaluate independently against fresh copies"
    )
    rules: ValidationRuleConfig = Field(
        default_factory=ValidationRuleConfig,
        description="Validation rule toggles to apply during the evaluation"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Optional evaluation execution flags"
    )


class DatasetResponse(BaseModel):
    """Response returned upon dataset upload or retrieval."""
    model_config = ConfigDict(extra="ignore")

    dataset_id: str
    filename: str
    uploaded_at: datetime
    profile: DatasetProfile
    is_sales_compatible: bool
    is_manufacturing_compatible: bool = False
    detected_domain: str = "sales"
    supported_domains: List[Dict[str, Any]] = Field(default_factory=list)
    domain_compatibility: Dict[str, bool] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class EvaluationSummaryItem(BaseModel):
    """Summary record of a persisted evaluation run."""
    model_config = ConfigDict(extra="ignore")

    report_id: str
    dataset_id: str
    created_at: datetime
    total_attempted: int
    successfully_applied: int
    detected_mutations: int
    surviving_mutations: int
    failed_evaluations: int
    mutation_score: Optional[float]


class HealthResponse(BaseModel):
    """Application health and version information."""
    status: str = "ok"
    app: str = "DataTripwire"
    version: str = "0.1.0"
    environment: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized API error response body."""
    error: str
    detail: str
    code: str
