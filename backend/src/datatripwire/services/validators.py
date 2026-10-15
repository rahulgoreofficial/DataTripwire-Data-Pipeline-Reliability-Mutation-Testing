"""Baseline and configurable data validation engine for DataTripwire.

Executes data-quality checks on tabular datasets and produces structured
ValidationFinding records with stable machine-readable rule codes.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Set
import pandas as pd

from datatripwire.config import SALES_SCHEMA_COLUMNS
from datatripwire.domain.enums import FindingSeverity, RuleType
from datatripwire.domain.models import ValidationFinding
from datatripwire.schemas import ValidationRuleConfig


# Stable machine-readable rule codes
RULE_CODE_REQUIRED_COLUMN_MISSING = "REQUIRED_COLUMN_MISSING"
RULE_CODE_REQUIRED_VALUE_MISSING = "REQUIRED_VALUE_MISSING"
RULE_CODE_QUANTITY_NOT_POSITIVE = "QUANTITY_NOT_POSITIVE"
RULE_CODE_UNIT_PRICE_NEGATIVE = "UNIT_PRICE_NEGATIVE"
RULE_CODE_INVALID_TRANSACTION_DATE = "INVALID_TRANSACTION_DATE"
RULE_CODE_TRANSACTION_ID_DUPLICATE = "TRANSACTION_ID_DUPLICATE"
RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH = "EXPECTED_ROW_COUNT_MISMATCH"


def compute_finding_fingerprint(finding: ValidationFinding) -> str:
    """Compute a stable, normalized fingerprint for matching findings between runs."""
    records_part = ",".join(sorted(finding.affected_record_ids)) if finding.affected_record_ids else ""
    col_part = finding.affected_column or ""
    return f"{finding.rule_id}::{finding.rule_type.value}::{col_part}::{records_part}"


def run_validation(
    df: pd.DataFrame,
    config: Optional[ValidationRuleConfig] = None,
    reference_row_count: Optional[int] = None,
) -> List[ValidationFinding]:
    """Execute configured validation rules on a dataset.
    
    Args:
        df: Tabular dataset DataFrame.
        config: Rule activation configuration. Defaults to baseline rules if omitted.
        reference_row_count: Optional expected row count for row-count reconciliation.
        
    Returns:
        List of ValidationFinding instances.
    """
    rule_config = config or ValidationRuleConfig()
    findings: List[ValidationFinding] = []
    finding_idx = 1

    # Helper to get record IDs safely
    def get_record_id(row_idx: int) -> str:
        if "transaction_id" in df.columns:
            val = df.at[row_idx, "transaction_id"]
            if pd.notna(val) and str(val).strip():
                return str(val).strip()
        return f"row_{row_idx}"

    # 1. Required columns check
    if rule_config.check_required_columns:
        missing_cols = [c for c in SALES_SCHEMA_COLUMNS if c not in df.columns]
        for col in missing_cols:
            findings.append(
                ValidationFinding(
                    finding_id=f"FIND-COL-{finding_idx}",
                    rule_id=RULE_CODE_REQUIRED_COLUMN_MISSING,
                    rule_type=RuleType.DATA_TYPE,
                    severity=FindingSeverity.CRITICAL,
                    affected_column=col,
                    affected_record_ids=[],
                    explanation=f"Required canonical column '{col}' is missing from the dataset.",
                    detected=True,
                )
            )
            finding_idx += 1

    # 2. Required values not missing check
    if rule_config.check_required_values:
        cols_to_check = [c for c in SALES_SCHEMA_COLUMNS if c in df.columns]
        for col in cols_to_check:
            null_mask = df[col].isna()
            if null_mask.any():
                violating_indices = df.index[null_mask].tolist()
                violating_ids = [get_record_id(idx) for idx in violating_indices]
                findings.append(
                    ValidationFinding(
                        finding_id=f"FIND-VAL-{finding_idx}",
                        rule_id=RULE_CODE_REQUIRED_VALUE_MISSING,
                        rule_type=RuleType.NOT_NULL,
                        severity=FindingSeverity.ERROR,
                        affected_column=col,
                        affected_record_ids=violating_ids,
                        explanation=f"Required column '{col}' contains missing (null/NaN) values in {len(violating_ids)} record(s).",
                        detected=True,
                    )
                )
                finding_idx += 1

    # 3. Quantity is positive check (quantity > 0)
    if rule_config.check_quantity_positive and "quantity" in df.columns:
        violating_ids: List[str] = []
        for idx, val in df["quantity"].items():
            if pd.isna(val):
                continue
            try:
                num = float(val)
                if num <= 0:
                    violating_ids.append(get_record_id(idx))
            except Exception:
                violating_ids.append(get_record_id(idx))

        if violating_ids:
            findings.append(
                ValidationFinding(
                    finding_id=f"FIND-QTY-{finding_idx}",
                    rule_id=RULE_CODE_QUANTITY_NOT_POSITIVE,
                    rule_type=RuleType.VALUE_RANGE,
                    severity=FindingSeverity.ERROR,
                    affected_column="quantity",
                    affected_record_ids=violating_ids,
                    explanation=f"Column 'quantity' contains non-positive or non-numeric values in {len(violating_ids)} record(s).",
                    detected=True,
                )
            )
            finding_idx += 1

    # 4. Unit price is non-negative check (unit_price >= 0)
    if rule_config.check_unit_price_nonnegative and "unit_price" in df.columns:
        violating_ids = []
        for idx, val in df["unit_price"].items():
            if pd.isna(val):
                continue
            try:
                num = Decimal(str(val))
                if num < Decimal("0.00"):
                    violating_ids.append(get_record_id(idx))
            except Exception:
                violating_ids.append(get_record_id(idx))

        if violating_ids:
            findings.append(
                ValidationFinding(
                    finding_id=f"FIND-PRC-{finding_idx}",
                    rule_id=RULE_CODE_UNIT_PRICE_NEGATIVE,
                    rule_type=RuleType.VALUE_RANGE,
                    severity=FindingSeverity.ERROR,
                    affected_column="unit_price",
                    affected_record_ids=violating_ids,
                    explanation=f"Column 'unit_price' contains negative monetary values in {len(violating_ids)} record(s).",
                    detected=True,
                )
            )
            finding_idx += 1

    # 5. Transaction date validity check (ISO format YYYY-MM-DD)
    if rule_config.check_valid_transaction_date and "transaction_date" in df.columns:
        violating_ids = []
        for idx, val in df["transaction_date"].items():
            if pd.isna(val):
                continue
            date_str = str(val).strip()
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                if parsed.year < 1900 or parsed.year > 2100:
                    violating_ids.append(get_record_id(idx))
            except Exception:
                violating_ids.append(get_record_id(idx))

        if violating_ids:
            findings.append(
                ValidationFinding(
                    finding_id=f"FIND-DATE-{finding_idx}",
                    rule_id=RULE_CODE_INVALID_TRANSACTION_DATE,
                    rule_type=RuleType.DATE_VALIDITY,
                    severity=FindingSeverity.ERROR,
                    affected_column="transaction_date",
                    affected_record_ids=violating_ids,
                    explanation=f"Column 'transaction_date' contains invalid or non-ISO dates in {len(violating_ids)} record(s).",
                    detected=True,
                )
            )
            finding_idx += 1

    # 6. Transaction uniqueness check (CONFIGURABLE - False in baseline)
    if rule_config.check_unique_transaction_id and "transaction_id" in df.columns:
        non_null_txn = df["transaction_id"].dropna().astype(str).str.strip()
        duplicate_mask = non_null_txn.duplicated(keep=False)
        if duplicate_mask.any():
            duplicate_ids = sorted(list(set(non_null_txn[duplicate_mask].tolist())))
            findings.append(
                ValidationFinding(
                    finding_id=f"FIND-DUP-{finding_idx}",
                    rule_id=RULE_CODE_TRANSACTION_ID_DUPLICATE,
                    rule_type=RuleType.UNIQUENESS,
                    severity=FindingSeverity.CRITICAL,
                    affected_column="transaction_id",
                    affected_record_ids=duplicate_ids,
                    explanation=f"Duplicate transaction_id values detected for {len(duplicate_ids)} distinct identifier(s): {duplicate_ids}",
                    detected=True,
                )
            )
            finding_idx += 1

    # 7. Expected row count check (CONFIGURABLE - False in baseline)
    if rule_config.check_expected_row_count:
        expected = rule_config.expected_row_count if rule_config.expected_row_count is not None else reference_row_count
        if expected is not None and len(df) != expected:
            findings.append(
                ValidationFinding(
                    finding_id=f"FIND-ROW-{finding_idx}",
                    rule_id=RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH,
                    rule_type=RuleType.VALUE_RANGE,
                    severity=FindingSeverity.ERROR,
                    affected_column=None,
                    affected_record_ids=[],
                    explanation=f"Row count mismatch: expected {expected} records, but observed {len(df)} records.",
                    detected=True,
                )
            )
            finding_idx += 1

    return findings
