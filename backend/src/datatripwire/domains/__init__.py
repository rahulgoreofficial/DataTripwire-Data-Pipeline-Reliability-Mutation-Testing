"""Domain architecture package for DataTripwire.

Exports domain profiles, base classes, and domain registry.
"""

from datatripwire.domains.base import BaseDomainProfile
from datatripwire.domains.general import GeneralDomainProfile
from datatripwire.domains.manufacturing import (
    ManufacturingDomainProfile,
    RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH,
    RULE_CODE_MFG_INVALID_TIMESTAMP,
    RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE,
    RULE_CODE_MFG_MEASUREMENT_NEGATIVE,
    RULE_CODE_MFG_PRODUCTION_INCONSISTENCY,
    RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS,
    RULE_CODE_MFG_READING_ID_DUPLICATE,
    RULE_CODE_MFG_REQUIRED_COLUMN_MISSING,
    RULE_CODE_MFG_REQUIRED_VALUE_MISSING,
    RULE_CODE_MFG_SENSOR_NUMERIC_INVALID,
    RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS,
)
from datatripwire.domains.registry import DomainRegistry, get_domain_registry
from datatripwire.domains.sales import SalesDomainProfile

__all__ = [
    "BaseDomainProfile",
    "SalesDomainProfile",
    "ManufacturingDomainProfile",
    "GeneralDomainProfile",
    "DomainRegistry",
    "get_domain_registry",
    "RULE_CODE_MFG_REQUIRED_COLUMN_MISSING",
    "RULE_CODE_MFG_REQUIRED_VALUE_MISSING",
    "RULE_CODE_MFG_READING_ID_DUPLICATE",
    "RULE_CODE_MFG_MACHINE_TIMESTAMP_DUPLICATE",
    "RULE_CODE_MFG_INVALID_TIMESTAMP",
    "RULE_CODE_MFG_SENSOR_NUMERIC_INVALID",
    "RULE_CODE_MFG_MEASUREMENT_NEGATIVE",
    "RULE_CODE_MFG_QUALITY_PERCENTAGE_OUT_OF_BOUNDS",
    "RULE_CODE_MFG_PRODUCTION_INCONSISTENCY",
    "RULE_CODE_MFG_TEMPERATURE_OUT_OF_BOUNDS",
    "RULE_CODE_MFG_EXPECTED_RECORD_COUNT_MISMATCH",
]
