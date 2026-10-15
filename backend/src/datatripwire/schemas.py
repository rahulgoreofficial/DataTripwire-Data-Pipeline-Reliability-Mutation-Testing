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
    
    Default configuration reflects the baseline validation suite:
    - Basic data sanity checks are enabled.
    - Transaction uniqueness is DISABLED by default (enabling duplicate fault demonstration).
    - Expected row count is DISABLED by default.
    """
    model_config = ConfigDict(extra="forbid")

    check_required_columns: bool = Field(default=True, description="Verify all canonical sales columns are present")
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


class MutationRequestItem(BaseModel):
    """Specification of an individual requested mutation in an evaluation batch."""
    model_config = ConfigDict(extra="allow")

    mutation_type: MutationType = Field(..., description="Category of mutation to inject")
    target_transaction_id: Optional[str] = Field(
        default=None,
        description="Target transaction ID for row-specific mutations (e.g., ORD-102)"
    )
    target_column: Optional[str] = Field(
        default=None,
        description="Target column name for column mutations (e.g., quantity, unit_price)"
    )
    value: Optional[Any] = Field(
        default=None,
        description="Custom injected value (e.g., 0 for invalid quantity, -100 for negative price)"
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
            if val_clean == "drop_row":
                return MutationType.DROPPED_ROW
            return MutationType(val_clean)
        return v


class EvaluationCreateRequest(BaseModel):
    """Request payload to initiate a mutation evaluation batch against a dataset."""
    model_config = ConfigDict(extra="forbid")

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
