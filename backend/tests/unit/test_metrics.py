"""Unit tests for business metrics engine.

Verifies:
1. Exact total revenue calculations using Decimal arithmetic.
2. Distinct customer counts and total transaction counts.
3. Excluded rows handling for non-numeric/null values.
4. Downstream metric impact deltas (absolute and percentage change).
5. Zero-baseline percentage calculation safety.
"""

from decimal import Decimal
import pandas as pd
import pytest

from datatripwire.domain.models import PipelineMetrics
from datatripwire.exceptions import IncompatibleSchemaError
from datatripwire.services.metrics import calculate_metric_deltas, calculate_sales_metrics


class TestMetrics:
    """Test suite for metrics calculation."""

    def test_calculate_metrics_from_clean_data(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-101", "ORD-102", "ORD-103"],
            "customer_id": ["CUST-1", "CUST-2", "CUST-1"],
            "quantity": [2, 1, 3],
            "unit_price": [500.0, 800.0, 200.0],
            "transaction_date": ["2026-03-01", "2026-03-01", "2026-03-02"],
        })
        metrics = calculate_sales_metrics(df)
        assert metrics.total_revenue == Decimal("2400.00")
        assert metrics.transaction_count == 3
        assert metrics.customer_count == 2
        assert metrics.average_order_value == Decimal("800.00")
        assert metrics.additional_metrics["completeness"] == "complete"
        assert metrics.additional_metrics["excluded_rows"] == 0

    def test_handles_partial_corrupted_rows(self):
        df = pd.DataFrame({
            "transaction_id": ["ORD-1", "ORD-2", "ORD-3"],
            "customer_id": ["C-1", "C-2", "C-3"],
            "quantity": [2, None, 1],  # Row 2 missing quantity
            "unit_price": [100.0, 200.0, 300.0],
            "transaction_date": ["2026-03-01", "2026-03-01", "2026-03-02"],
        })
        metrics = calculate_sales_metrics(df)
        # Revenue should compute only from valid rows (2*100 + 1*300 = 500.00)
        assert metrics.total_revenue == Decimal("500.00")
        assert metrics.transaction_count == 3
        assert metrics.additional_metrics["completeness"] == "partial"
        assert metrics.additional_metrics["excluded_rows"] == 1

    def test_raises_on_missing_required_columns(self):
        df = pd.DataFrame({"random_col": [1, 2]})
        with pytest.raises(IncompatibleSchemaError):
            calculate_sales_metrics(df)

    def test_calculate_metric_deltas_normal(self):
        baseline = PipelineMetrics(
            total_revenue=Decimal("2400.00"),
            transaction_count=3,
            customer_count=3,
        )
        mutated = PipelineMetrics(
            total_revenue=Decimal("3200.00"),
            transaction_count=4,
            customer_count=3,
        )
        deltas = calculate_metric_deltas(baseline, mutated)
        assert deltas["revenue_delta_abs"] == "800.00"
        assert deltas["revenue_delta_pct"] == 33.33
        assert deltas["transaction_count_delta"] == 1
        assert deltas["customer_count_delta"] == 0

    def test_calculate_metric_deltas_with_zero_baseline(self):
        baseline = PipelineMetrics(
            total_revenue=Decimal("0.00"),
            transaction_count=0,
            customer_count=0,
        )
        mutated = PipelineMetrics(
            total_revenue=Decimal("500.00"),
            transaction_count=1,
            customer_count=1,
        )
        deltas = calculate_metric_deltas(baseline, mutated)
        assert deltas["revenue_delta_abs"] == "500.00"
        # Avoid division by zero
        assert deltas["revenue_delta_pct"] is None
