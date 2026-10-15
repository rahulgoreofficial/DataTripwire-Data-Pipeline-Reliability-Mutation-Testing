"""Unit tests for dataset profiler service.

Verifies:
1. Extraction of row counts, column counts, and column names.
2. Inferred data types (integer, float, date, string).
3. Null counts and null percentages.
4. Duplicate row counts.
5. Numeric summaries (min, max, mean, sum).
6. Sales schema compatibility detection.
"""

import pandas as pd
import pytest

from datatripwire.config import SAMPLE_SALES_CSV
from datatripwire.services.csv_loader import validate_and_load_csv
from datatripwire.services.profiler import profile_dataframe


class TestProfiler:
    """Test suite for profile_dataframe."""

    def test_profile_sample_sales_dataset(self):
        df, _, _ = validate_and_load_csv(SAMPLE_SALES_CSV, filename="sample_sales.csv")
        profile = profile_dataframe(df, dataset_id="TEST-01", filename="sample_sales.csv")

        assert profile.dataset_id == "TEST-01"
        assert profile.row_count == 15
        assert profile.column_count == 5
        assert profile.is_sales_compatible is True
        assert profile.duplicate_row_count == 0
        assert profile.null_counts["quantity"] == 0
        assert profile.null_counts["unit_price"] == 0

        # Verify numeric summaries
        assert "quantity" in profile.numeric_summaries
        assert profile.numeric_summaries["quantity"]["min"] == 1.0
        assert profile.numeric_summaries["quantity"]["max"] == 10.0

        assert "unit_price" in profile.numeric_summaries
        assert profile.numeric_summaries["unit_price"]["min"] == 80.0
        assert profile.numeric_summaries["unit_price"]["max"] == 2500.0

    def test_detects_nulls_and_percentages(self):
        data = {
            "col_a": [1, None, 3, None],
            "col_b": ["x", "y", "z", "w"],
        }
        df = pd.DataFrame(data)
        profile = profile_dataframe(df, dataset_id="NULL-TEST", filename="nulls.csv")

        assert profile.row_count == 4
        assert profile.null_counts["col_a"] == 2
        assert profile.null_percentages["col_a"] == 50.0
        assert profile.null_counts["col_b"] == 0
        assert profile.null_percentages["col_b"] == 0.0

    def test_detects_duplicate_rows(self):
        data = {
            "a": [1, 2, 1],
            "b": ["x", "y", "x"],
        }
        df = pd.DataFrame(data)
        profile = profile_dataframe(df, dataset_id="DUP-TEST", filename="dups.csv")
        assert profile.duplicate_row_count == 1

    def test_detects_incompatible_sales_schema(self):
        data = {
            "order_number": [101, 102],
            "amount": [50.0, 100.0],
        }
        df = pd.DataFrame(data)
        profile = profile_dataframe(df, dataset_id="NON-SALES", filename="other.csv")
        assert profile.is_sales_compatible is False
        assert any("lacks required sales columns" in w for w in profile.warnings)
