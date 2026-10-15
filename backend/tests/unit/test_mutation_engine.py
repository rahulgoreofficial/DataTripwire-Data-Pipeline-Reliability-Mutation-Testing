"""Unit tests for the synthetic mutation engine.

Verifies:
1. All five mutation operators: duplicate_row, missing_required_value, invalid_quantity, invalid_unit_price, dropped_row.
2. Metadata returned accurately describes the change.
3. Immutability of the source DataFrame.
4. Nonexistent and ambiguous targets return structured failure without raising unhandled exceptions.
5. No-op mutations are rejected as unapplied.
"""

import numpy as np
import pandas as pd
import pytest

from datatripwire.domain.enums import MutationType
from datatripwire.domain.models import MutationSpec
from datatripwire.services.mutation_engine import apply_mutation


@pytest.fixture
def clean_sample_df():
    """Provides a fresh, clean 3-row sales DataFrame."""
    return pd.DataFrame({
        "transaction_id": ["ORD-101", "ORD-102", "ORD-103"],
        "customer_id": ["CUST-1", "CUST-2", "CUST-3"],
        "quantity": [2, 1, 3],
        "unit_price": [500.0, 800.0, 200.0],
        "transaction_date": ["2026-03-01", "2026-03-01", "2026-03-02"],
    })


class TestMutationEngine:
    """Test suite for apply_mutation."""

    def test_duplicate_row_mutation(self, clean_sample_df):
        spec = MutationSpec(
            mutation_id="MUT-01",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="ORD-102",
            description="Duplicate ORD-102",
        )
        mutated_df, meta = apply_mutation(clean_sample_df, spec)

        assert meta["applied"] is True
        assert len(mutated_df) == 4
        assert len(clean_sample_df) == 3  # Immutability check
        assert mutated_df["transaction_id"].value_counts()["ORD-102"] == 2
        assert meta["affected_record_ids"] == ["ORD-102"]
        assert meta["expected_rule_code"] == "TRANSACTION_ID_DUPLICATE"

    def test_missing_required_value_mutation(self, clean_sample_df):
        spec = MutationSpec(
            mutation_id="MUT-02",
            mutation_type=MutationType.MISSING_REQUIRED_VALUE,
            target_record_id="ORD-101",
            target_column="customer_id",
            description="Nullify customer_id on ORD-101",
        )
        mutated_df, meta = apply_mutation(clean_sample_df, spec)

        assert meta["applied"] is True
        assert len(mutated_df) == 3
        assert pd.isna(mutated_df.loc[mutated_df["transaction_id"] == "ORD-101", "customer_id"].iloc[0])
        assert clean_sample_df.loc[clean_sample_df["transaction_id"] == "ORD-101", "customer_id"].iloc[0] == "CUST-1"
        assert meta["expected_rule_code"] == "REQUIRED_VALUE_MISSING"

    def test_invalid_quantity_mutation(self, clean_sample_df):
        spec = MutationSpec(
            mutation_id="MUT-03",
            mutation_type=MutationType.INVALID_QUANTITY,
            target_record_id="ORD-103",
            params={"value": 0},
            description="Set quantity to 0 on ORD-103",
        )
        mutated_df, meta = apply_mutation(clean_sample_df, spec)

        assert meta["applied"] is True
        assert mutated_df.loc[mutated_df["transaction_id"] == "ORD-103", "quantity"].iloc[0] == 0
        assert clean_sample_df.loc[clean_sample_df["transaction_id"] == "ORD-103", "quantity"].iloc[0] == 3
        assert meta["expected_rule_code"] == "QUANTITY_NOT_POSITIVE"

    def test_invalid_unit_price_mutation(self, clean_sample_df):
        spec = MutationSpec(
            mutation_id="MUT-04",
            mutation_type=MutationType.INVALID_UNIT_PRICE,
            target_record_id="ORD-101",
            params={"value": -150.0},
            description="Set negative price on ORD-101",
        )
        mutated_df, meta = apply_mutation(clean_sample_df, spec)

        assert meta["applied"] is True
        assert mutated_df.loc[mutated_df["transaction_id"] == "ORD-101", "unit_price"].iloc[0] == -150.0
        assert clean_sample_df.loc[clean_sample_df["transaction_id"] == "ORD-101", "unit_price"].iloc[0] == 500.0
        assert meta["expected_rule_code"] == "UNIT_PRICE_NEGATIVE"

    def test_dropped_row_mutation(self, clean_sample_df):
        spec = MutationSpec(
            mutation_id="MUT-05",
            mutation_type=MutationType.DROPPED_ROW,
            target_record_id="ORD-102",
            description="Drop record ORD-102",
        )
        mutated_df, meta = apply_mutation(clean_sample_df, spec)

        assert meta["applied"] is True
        assert len(mutated_df) == 2
        assert len(clean_sample_df) == 3
        assert "ORD-102" not in mutated_df["transaction_id"].values
        assert meta["expected_rule_code"] == "EXPECTED_ROW_COUNT_MISMATCH"

    def test_nonexistent_target_returns_failure(self, clean_sample_df):
        spec = MutationSpec(
            mutation_id="MUT-06",
            mutation_type=MutationType.DUPLICATE_ROW,
            target_record_id="NONEXISTENT-999",
            description="Duplicate missing ID",
        )
        mutated_df, meta = apply_mutation(clean_sample_df, spec)

        assert meta["applied"] is False
        assert "not found" in meta["failure_reason"].lower()
        assert len(mutated_df) == len(clean_sample_df)

    def test_ambiguous_target_returns_failure(self):
        dup_df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-101"],
            "customer_id": ["C1", "C2"],
            "quantity": [1, 1],
            "unit_price": [10.0, 10.0],
            "transaction_date": ["2026-03-01", "2026-03-01"],
        })
        spec = MutationSpec(
            mutation_id="MUT-07",
            mutation_type=MutationType.INVALID_QUANTITY,
            target_record_id="ORD-101",
            description="Target ambiguous ID",
        )
        _, meta = apply_mutation(dup_df, spec)
        assert meta["applied"] is False
        assert "ambiguous" in meta["failure_reason"].lower()

    def test_no_op_mutation_returns_failure(self):
        null_df = pd.DataFrame({
            "transaction_id": ["ORD-101"],
            "customer_id": ["C1"],
            "quantity": [np.nan],  # Already null!
            "unit_price": [10.0],
            "transaction_date": ["2026-03-01"],
        })
        spec = MutationSpec(
            mutation_id="MUT-08",
            mutation_type=MutationType.MISSING_REQUIRED_VALUE,
            target_record_id="ORD-101",
            target_column="quantity",
            description="Set already null cell to null",
        )
        _, meta = apply_mutation(null_df, spec)
        assert meta["applied"] is False
        assert "already missing" in meta["failure_reason"].lower()
