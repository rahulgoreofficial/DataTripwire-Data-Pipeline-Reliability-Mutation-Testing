"""Domain enumerations for DataTripwire.

These enums standardize mutation types, rule categories, finding severities,
and evaluation statuses across all phases of the platform.
"""

from enum import Enum


class DataDomain(str, Enum):
    """Supported data domains in DataTripwire."""
    SALES = "sales"
    MANUFACTURING = "manufacturing"
    GENERAL = "general"


class MutationType(str, Enum):
    """Supported categories of synthetic data mutations.
    
    Each category targets a distinct vulnerability in data pipelines.
    """
    # Sales Mutations
    DUPLICATE_ROW = "duplicate_row"
    MISSING_REQUIRED_VALUE = "missing_required_value"
    INVALID_QUANTITY = "invalid_quantity"
    INVALID_UNIT_PRICE = "invalid_unit_price"
    DROPPED_ROW = "dropped_row"

    # Manufacturing Mutations
    DUPLICATE_SENSOR_READING = "duplicate_sensor_reading"
    MISSING_SENSOR_VALUE = "missing_sensor_value"
    INVALID_SENSOR_VALUE = "invalid_sensor_value"
    DROPPED_SENSOR_READING = "dropped_sensor_reading"
    INVALID_PRODUCTION_VALUE = "invalid_production_value"


class FindingSeverity(str, Enum):
    """Severity classification for validation findings."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleType(str, Enum):
    """Categorization of data-quality rules."""
    UNIQUENESS = "uniqueness"
    NOT_NULL = "not_null"
    VALUE_RANGE = "value_range"
    DATA_TYPE = "data_type"
    DATE_VALIDITY = "date_validity"
    CONSISTENCY = "consistency"


class RecommendationStatus(str, Enum):
    """Lifecycle status of a generated rule recommendation."""
    SUGGESTED = "suggested"
    APPLIED = "applied"
    DISMISSED = "dismissed"


class EvaluationStatus(str, Enum):
    """High-level outcome for a mutation test."""
    DETECTED = "detected"
    ESCAPED = "escaped"
    INAPPLICABLE = "inapplicable"
    FAILED = "failed"
