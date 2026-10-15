"""Business metrics calculation service for sales pipelines.

Computes total revenue, transaction counts, distinct customer counts,
average order value, and excluded non-contributing records using high-precision
Decimal arithmetic.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, Optional, Tuple
import pandas as pd

from datatripwire.domain.models import PipelineMetrics
from datatripwire.exceptions import IncompatibleSchemaError


def _safe_to_decimal(val: Any) -> Optional[Decimal]:
    """Safely convert a cell value to Decimal, returning None if NaN, null, or invalid."""
    if pd.isna(val):
        return None
    try:
        # Convert through string to avoid float binary artifacts
        return Decimal(str(val).strip())
    except Exception:
        return None


def calculate_sales_metrics(df: pd.DataFrame) -> PipelineMetrics:
    """Calculate sales business metrics from a tabular dataset.
    
    Formula:
        revenue = SUM(quantity * unit_price)
        
    Handles corrupted or partial rows explicitly by excluding them from revenue
    and reporting the excluded row count and completeness status in additional_metrics.
    
    Raises:
        IncompatibleSchemaError if required sales columns are missing.
    """
    required = ["quantity", "unit_price"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise IncompatibleSchemaError(missing)

    total_revenue = Decimal("0.00")
    valid_rows_for_revenue = 0
    excluded_rows = 0
    warnings = []

    for idx, row in df.iterrows():
        qty_dec = _safe_to_decimal(row["quantity"])
        price_dec = _safe_to_decimal(row["unit_price"])

        if qty_dec is None or price_dec is None:
            excluded_rows += 1
            continue

        # Accumulate row revenue
        row_rev = qty_dec * price_dec
        total_revenue += row_rev
        valid_rows_for_revenue += 1

    total_revenue = total_revenue.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total_transactions = int(len(df))

    # Customer count
    if "customer_id" in df.columns:
        customer_count = int(df["customer_id"].dropna().nunique())
    else:
        customer_count = 0
        warnings.append("customer_id column missing; customer_count is 0")

    # Completeness status
    if excluded_rows == 0:
        completeness = "complete"
    elif valid_rows_for_revenue > 0:
        completeness = "partial"
        warnings.append(f"{excluded_rows} row(s) contained invalid/missing quantity or price and were excluded from revenue")
    else:
        completeness = "incomplete"
        warnings.append("No valid rows could contribute to revenue calculation")

    additional = {
        "completeness": completeness,
        "valid_revenue_rows": valid_rows_for_revenue,
        "excluded_rows": excluded_rows,
        "warnings": warnings,
    }

    return PipelineMetrics(
        total_revenue=total_revenue,
        transaction_count=total_transactions,
        customer_count=customer_count,
        additional_metrics=additional,
    )


def calculate_metric_deltas(
    baseline: PipelineMetrics,
    mutated: PipelineMetrics,
) -> Dict[str, Any]:
    """Compute downstream business impact deltas between baseline and mutated metrics.
    
    Handles zero baselines gracefully for percentage computations.
    """
    revenue_delta_abs = (mutated.total_revenue - baseline.total_revenue).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    if baseline.total_revenue != Decimal("0.00"):
        rev_pct = round(
            float((revenue_delta_abs / baseline.total_revenue) * Decimal("100.0")), 2
        )
    else:
        rev_pct = None

    transaction_delta = mutated.transaction_count - baseline.transaction_count
    customer_delta = mutated.customer_count - baseline.customer_count

    aov_delta_abs = None
    aov_pct = None
    if baseline.average_order_value is not None and mutated.average_order_value is not None:
        aov_delta_abs = (mutated.average_order_value - baseline.average_order_value).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if baseline.average_order_value != Decimal("0.00"):
            aov_pct = round(
                float((aov_delta_abs / baseline.average_order_value) * Decimal("100.0")), 2
            )

    return {
        "revenue_baseline": str(baseline.total_revenue),
        "revenue_mutated": str(mutated.total_revenue),
        "revenue_delta_abs": str(revenue_delta_abs),
        "revenue_delta_pct": rev_pct,
        "transaction_count_baseline": baseline.transaction_count,
        "transaction_count_mutated": mutated.transaction_count,
        "transaction_count_delta": transaction_delta,
        "customer_count_baseline": baseline.customer_count,
        "customer_count_mutated": mutated.customer_count,
        "customer_count_delta": customer_delta,
        "aov_baseline": str(baseline.average_order_value) if baseline.average_order_value else None,
        "aov_mutated": str(mutated.average_order_value) if mutated.average_order_value else None,
        "aov_delta_abs": str(aov_delta_abs) if aov_delta_abs is not None else None,
        "aov_delta_pct": aov_pct,
    }
