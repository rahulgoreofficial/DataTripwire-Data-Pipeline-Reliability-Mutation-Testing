"""Tests for the deterministic clean sample sales dataset.

Verifies:
1. The sample sales CSV exists and is readable.
2. The dataset strictly adheres to the documented schema.
3. Transaction identifiers are completely unique in the clean baseline.
4. Quantities are strictly positive integers.
5. Unit prices are non-negative monetary values.
6. Transaction dates are valid, parseable ISO dates.
7. Documented baseline transaction count, customer count, and total revenue
   match the actual data to the exact rupee/cent.
8. The 3-transaction demonstration subset (ORD-101, ORD-102, ORD-103)
   accurately yields the illustrative ₹2,400.00 revenue.
"""

import csv
from datetime import datetime
from decimal import Decimal
import pandas as pd
import pytest

from datatripwire.config import (
    SALES_SCHEMA_COLUMNS,
    SAMPLE_DATASET_BASELINE,
    SAMPLE_SALES_CSV,
)
from datatripwire.domain.models import PipelineMetrics


class TestSampleSalesData:
    """Tests evaluating the synthetic clean sales dataset fixture."""

    def test_file_exists(self):
        assert SAMPLE_SALES_CSV.is_file(), f"Sample dataset not found at {SAMPLE_SALES_CSV}"

    def test_load_with_standard_csv(self):
        with open(SAMPLE_SALES_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == SAMPLE_DATASET_BASELINE["row_count"]

    def test_load_with_pandas(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        assert len(df) == SAMPLE_DATASET_BASELINE["row_count"]
        assert list(df.columns) == SALES_SCHEMA_COLUMNS

    def test_column_schema(self):
        with open(SAMPLE_SALES_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == SALES_SCHEMA_COLUMNS

    def test_transaction_id_uniqueness(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        txn_ids = df["transaction_id"].tolist()
        assert len(txn_ids) == len(set(txn_ids)), "Clean sample dataset contains duplicate transaction_id values"

    def test_positive_quantities(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        for idx, row in df.iterrows():
            qty = row["quantity"]
            assert int(qty) == qty, f"Row {idx}: quantity '{qty}' is not an integer"
            assert qty > 0, f"Row {idx}: quantity '{qty}' is not positive"

    def test_non_negative_unit_prices(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        for idx, row in df.iterrows():
            price = Decimal(str(row["unit_price"]))
            assert price >= Decimal("0.00"), f"Row {idx}: unit_price '{price}' is negative"

    def test_valid_transaction_dates(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        for idx, row in df.iterrows():
            date_str = str(row["transaction_date"])
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                assert parsed.year >= 2020
            except ValueError as err:
                pytest.fail(f"Row {idx}: invalid date format '{date_str}': {err}")

    def test_customer_count_and_repeats(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        unique_customers = df["customer_id"].nunique()
        assert unique_customers == SAMPLE_DATASET_BASELINE["unique_customer_count"]
        # Confirm some customers have multiple transactions
        customer_counts = df["customer_id"].value_counts()
        assert (customer_counts > 1).any(), "Sample dataset should contain repeated customers for realism"

    def test_baseline_transaction_count_and_revenue_match(self):
        df = pd.read_csv(SAMPLE_SALES_CSV)
        
        # Calculate revenue with exact Decimal precision
        total_rev = Decimal("0.00")
        for _, row in df.iterrows():
            qty = Decimal(str(row["quantity"]))
            price = Decimal(str(row["unit_price"]))
            total_rev += qty * price

        expected_rev = Decimal(SAMPLE_DATASET_BASELINE["expected_revenue"])
        expected_count = SAMPLE_DATASET_BASELINE["expected_transaction_count"]

        assert len(df) == expected_count
        assert total_rev == expected_rev

        # Also test mapping into PipelineMetrics
        metrics = PipelineMetrics(
            total_revenue=total_rev,
            transaction_count=len(df),
            customer_count=df["customer_id"].nunique(),
        )
        assert metrics.total_revenue == Decimal("19000.00")
        assert metrics.transaction_count == 15
        assert metrics.customer_count == 10
        # AOV = 19000.00 / 15 = 1266.67
        assert metrics.average_order_value == Decimal("1266.67")

    def test_illustrative_scenario_subset_revenue(self):
        """Verifies the 3-transaction scenario from product definition (ORD-101, ORD-102, ORD-103)."""
        df = pd.read_csv(SAMPLE_SALES_CSV)
        subset = df[df["transaction_id"].isin(["ORD-101", "ORD-102", "ORD-103"])]
        assert len(subset) == 3

        subset_rev = Decimal("0.00")
        for _, row in subset.iterrows():
            qty = Decimal(str(row["quantity"]))
            price = Decimal(str(row["unit_price"]))
            subset_rev += qty * price

        # Expected illustrative revenue = ₹2,400.00
        assert subset_rev == Decimal("2400.00")
