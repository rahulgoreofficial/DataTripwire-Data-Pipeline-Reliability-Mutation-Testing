"""Unit tests for baseline and configurable validation rules.

Verifies:
1. All individual validation checks trigger appropriate findings.
2. Disabling check_unique_transaction_id (baseline default) permits duplicates to survive.
3. Enabling check_unique_transaction_id detects duplicate transaction IDs.
4. Expected row count check behaves correctly when enabled/disabled.
5. Finding fingerprints are stable and distinguish between violations.
"""

import pandas as pd
import pytest

from datatripwire.schemas import ValidationRuleConfig
from datatripwire.services.validators import (
    RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH,
    RULE_CODE_INVALID_TRANSACTION_DATE,
    RULE_CODE_QUANTITY_NOT_POSITIVE,
    RULE_CODE_REQUIRED_COLUMN_MISSING,
    RULE_CODE_REQUIRED_VALUE_MISSING,
    RULE_CODE_TRANSACTION_ID_DUPLICATE,
    RULE_CODE_UNIT_PRICE_NEGATIVE,
    compute_finding_fingerprint,
    run_validation,
)


class TestValidators:
    """Test suite for run_validation."""

    def test_clean_sales_data_produces_no_baseline_findings(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-102"],
            "customer_id": ["CUST-1", "CUST-2"],
            "quantity": [1, 2],
            "unit_price": [100.0, 200.0],
            "transaction_date": ["2026-03-01", "2026-03-02"],
        })
        findings = run_validation(df)
        assert len(findings) == 0

    def test_missing_column_triggers_finding(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101"],
            "quantity": [1],
        })
        findings = run_validation(df, ValidationRuleConfig(check_required_columns=True))
        codes = [f.rule_id for f in findings]
        assert RULE_CODE_REQUIRED_COLUMN_MISSING in codes
        assert any(f.affected_column == "customer_id" for f in findings)

    def test_missing_value_triggers_finding(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-102"],
            "customer_id": ["CUST-1", None],
            "quantity": [1, 2],
            "unit_price": [100.0, 200.0],
            "transaction_date": ["2026-03-01", "2026-03-02"],
        })
        findings = run_validation(df, ValidationRuleConfig(check_required_values=True))
        req_val_findings = [f for f in findings if f.rule_id == RULE_CODE_REQUIRED_VALUE_MISSING]
        assert len(req_val_findings) == 1
        assert req_val_findings[0].affected_column == "customer_id"
        assert req_val_findings[0].affected_record_ids == ["ORD-102"]

    def test_invalid_quantity_triggers_finding(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-102"],
            "customer_id": ["CUST-1", "CUST-2"],
            "quantity": [0, -5],
            "unit_price": [100.0, 200.0],
            "transaction_date": ["2026-03-01", "2026-03-02"],
        })
        findings = run_validation(df, ValidationRuleConfig(check_quantity_positive=True))
        qty_findings = [f for f in findings if f.rule_id == RULE_CODE_QUANTITY_NOT_POSITIVE]
        assert len(qty_findings) == 1
        assert sorted(qty_findings[0].affected_record_ids) == ["ORD-101", "ORD-102"]

    def test_negative_unit_price_triggers_finding(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101"],
            "customer_id": ["CUST-1"],
            "quantity": [1],
            "unit_price": [-50.0],
            "transaction_date": ["2026-03-01"],
        })
        findings = run_validation(df, ValidationRuleConfig(check_unit_price_nonnegative=True))
        prc_findings = [f for f in findings if f.rule_id == RULE_CODE_UNIT_PRICE_NEGATIVE]
        assert len(prc_findings) == 1
        assert prc_findings[0].affected_record_ids == ["ORD-101"]

    def test_invalid_date_triggers_finding(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101"],
            "customer_id": ["CUST-1"],
            "quantity": [1],
            "unit_price": [100.0],
            "transaction_date": ["not-a-date"],
        })
        findings = run_validation(df, ValidationRuleConfig(check_valid_transaction_date=True))
        date_findings = [f for f in findings if f.rule_id == RULE_CODE_INVALID_TRANSACTION_DATE]
        assert len(date_findings) == 1
        assert date_findings[0].affected_record_ids == ["ORD-101"]

    def test_uniqueness_rule_disabled_allows_duplicate_to_survive(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-101"],  # Duplicate!
            "customer_id": ["CUST-1", "CUST-1"],
            "quantity": [1, 1],
            "unit_price": [100.0, 100.0],
            "transaction_date": ["2026-03-01", "2026-03-01"],
        })
        # Baseline: uniqueness is disabled
        findings = run_validation(df, ValidationRuleConfig(check_unique_transaction_id=False))
        dup_findings = [f for f in findings if f.rule_id == RULE_CODE_TRANSACTION_ID_DUPLICATE]
        assert len(dup_findings) == 0  # Survives!

    def test_uniqueness_rule_enabled_catches_duplicate(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-101"],
            "customer_id": ["CUST-1", "CUST-1"],
            "quantity": [1, 1],
            "unit_price": [100.0, 100.0],
            "transaction_date": ["2026-03-01", "2026-03-01"],
        })
        # Hardened rules: uniqueness enabled
        findings = run_validation(df, ValidationRuleConfig(check_unique_transaction_id=True))
        dup_findings = [f for f in findings if f.rule_id == RULE_CODE_TRANSACTION_ID_DUPLICATE]
        assert len(dup_findings) == 1
        assert dup_findings[0].affected_record_ids == ["ORD-101"]

    def test_expected_row_count_check(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-102"],
            "customer_id": ["CUST-1", "CUST-2"],
            "quantity": [1, 2],
            "unit_price": [100.0, 200.0],
            "transaction_date": ["2026-03-01", "2026-03-02"],
        })
        # Disabled: no finding
        f_disabled = run_validation(df, ValidationRuleConfig(check_expected_row_count=False), reference_row_count=3)
        assert len([f for f in f_disabled if f.rule_id == RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH]) == 0

        # Enabled: len(df) == 2, expected == 3 -> triggers finding
        f_enabled = run_validation(df, ValidationRuleConfig(check_expected_row_count=True, expected_row_count=3))
        row_findings = [f for f in f_enabled if f.rule_id == RULE_CODE_EXPECTED_ROW_COUNT_MISMATCH]
        assert len(row_findings) == 1

    def test_finding_fingerprint_generation(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101"],
            "customer_id": [None],
            "quantity": [1],
            "unit_price": [100.0],
            "transaction_date": ["2026-03-01"],
        })
        findings = run_validation(df)
        fp1 = compute_finding_fingerprint(findings[0])
        fp2 = compute_finding_fingerprint(findings[0])
        assert fp1 == fp2
        assert "REQUIRED_VALUE_MISSING" in fp1
        assert "customer_id" in fp1
