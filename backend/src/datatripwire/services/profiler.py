"""Dataset profiler service for DataTripwire.

Inspects pandas DataFrames to extract metadata, structural characteristics,
data types, null distributions, numeric summaries, and sales schema compatibility.
"""

from typing import Any, Dict, List
import numpy as np
import pandas as pd

from datatripwire.config import SALES_SCHEMA_COLUMNS
from datatripwire.domain.models import DatasetProfile


def _infer_column_type(series: pd.Series) -> str:
    """Infer high-level data type for a pandas Series."""
    # Drop NAs to test remaining non-null values
    non_nulls = series.dropna()
    if len(non_nulls) == 0:
        return "empty"

    dtype = str(series.dtype)
    if "int" in dtype:
        return "integer"
    if "float" in dtype:
        return "float"
    if "bool" in dtype:
        return "boolean"
    if "datetime" in dtype:
        return "date"

    # Attempt date parse on sample
    sample = str(non_nulls.iloc[0]).strip()
    if len(sample) == 10 and sample[4] == "-" and sample[7] == "-":
        try:
            pd.to_datetime(non_nulls.head(10), format="%Y-%m-%d")
            return "date"
        except Exception:
            pass

    # Check if string values are actually numeric
    try:
        pd.to_numeric(non_nulls.head(20))
        # If all can be cast to int
        converted = pd.to_numeric(non_nulls.head(20))
        if (converted % 1 == 0).all():
            return "integer"
        return "float"
    except Exception:
        pass

    return "string"


def profile_dataframe(df: pd.DataFrame, dataset_id: str, filename: str) -> DatasetProfile:
    """Generate a comprehensive DatasetProfile from a DataFrame.
    
    Args:
        df: The pandas DataFrame to inspect.
        dataset_id: Unique identifier for the dataset.
        filename: Original filename.
        
    Returns:
        DatasetProfile model populated with real data metrics.
    """
    row_count = int(len(df))
    column_count = int(len(df.columns))
    column_names = [str(c) for c in df.columns]

    column_types: Dict[str, str] = {}
    null_counts: Dict[str, int] = {}
    null_percentages: Dict[str, float] = {}
    numeric_summaries: Dict[str, Dict[str, float]] = {}
    warnings: List[str] = []

    for col in df.columns:
        series = df[col]
        col_str = str(col)

        # Nulls
        null_count = int(series.isna().sum())
        null_counts[col_str] = null_count
        null_percentage = round((null_count / row_count * 100.0), 2) if row_count > 0 else 0.0
        null_percentages[col_str] = null_percentage

        if null_percentage > 20.0:
            warnings.append(f"Column '{col_str}' has {null_percentage}% missing values.")

        # Types
        col_type = _infer_column_type(series)
        column_types[col_str] = col_type

        # Numeric summaries
        if col_type in ("integer", "float"):
            numeric_series = pd.to_numeric(series, errors="coerce").dropna()
            if len(numeric_series) > 0:
                numeric_summaries[col_str] = {
                    "min": float(round(numeric_series.min(), 2)),
                    "max": float(round(numeric_series.max(), 2)),
                    "mean": float(round(numeric_series.mean(), 2)),
                    "sum": float(round(numeric_series.sum(), 2)),
                }

    # Duplicate row counts across all columns
    duplicate_count = int(df.duplicated().sum())
    if duplicate_count > 0:
        warnings.append(f"Dataset contains {duplicate_count} duplicate row(s).")

    # Sales compatibility
    missing_sales_cols = [c for c in SALES_SCHEMA_COLUMNS if c not in df.columns]
    is_sales_compatible = len(missing_sales_cols) == 0

    if not is_sales_compatible:
        warnings.append(
            f"Dataset lacks required sales columns for mutation testing. Missing: {missing_sales_cols}"
        )

    return DatasetProfile(
        dataset_id=dataset_id,
        filename=filename,
        row_count=row_count,
        column_count=column_count,
        column_names=column_names,
        column_types=column_types,
        null_counts=null_counts,
        null_percentages=null_percentages,
        duplicate_row_count=duplicate_count,
        numeric_summaries=numeric_summaries,
        is_sales_compatible=is_sales_compatible,
        warnings=warnings,
    )
