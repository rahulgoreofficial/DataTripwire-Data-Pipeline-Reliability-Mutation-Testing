"""Unit tests for the CSV loader service.

Verifies:
1. Valid sales CSV loading.
2. Valid general tabular CSV loading.
3. Rejection of empty files.
4. Rejection of missing headers.
5. Rejection of duplicate headers.
6. Rejection of empty column names.
7. Rejection of non-CSV extensions.
8. Rejection of oversized files.
9. Rejection of excessive row and column counts.
10. Preservation of identifier strings (e.g. leading zeros).
"""

import pytest
from datatripwire.config import SAMPLE_SALES_CSV
from datatripwire.exceptions import FileTooLargeError, InvalidCSVError, LimitExceededError
from datatripwire.services.csv_loader import validate_and_load_csv


class TestCSVLoader:
    """Test suite for validate_and_load_csv."""

    def test_load_valid_sample_sales_csv(self):
        df, raw_bytes, warnings = validate_and_load_csv(
            file_source=SAMPLE_SALES_CSV,
            filename="sample_sales.csv",
        )
        assert len(df) == 15
        assert len(df.columns) == 5
        assert len(raw_bytes) > 0
        assert df["transaction_id"].iloc[0] == "ORD-101"

    def test_load_valid_general_csv(self):
        csv_data = b"id,name,category,value\n001,Widget,Hardware,49.99\n002,Gadget,Electronics,89.50\n"
        df, raw_bytes, warnings = validate_and_load_csv(
            file_source=csv_data,
            filename="inventory.csv",
        )
        assert len(df) == 2
        assert list(df.columns) == ["id", "name", "category", "value"]

    def test_preserves_leading_zeros_in_identifiers(self):
        csv_data = b"transaction_id,customer_id,quantity,unit_price,transaction_date\n00101,00201,2,500.00,2026-03-01\n"
        df, _, _ = validate_and_load_csv(file_source=csv_data, filename="sales.csv")
        assert df["transaction_id"].iloc[0] == "00101"
        assert df["customer_id"].iloc[0] == "00201"

    def test_rejects_non_csv_extension(self):
        with pytest.raises(InvalidCSVError, match="Unsupported file extension"):
            validate_and_load_csv(b"a,b\n1,2", filename="data.xlsx")

    def test_rejects_empty_file_bytes(self):
        with pytest.raises(InvalidCSVError, match="empty"):
            validate_and_load_csv(b"", filename="data.csv")

    def test_rejects_whitespace_only_file(self):
        with pytest.raises(InvalidCSVError, match="whitespace"):
            validate_and_load_csv(b"   \n\t  \n", filename="data.csv")

    def test_rejects_empty_column_name_in_header(self):
        csv_data = b"col1,,col3\n1,2,3\n"
        with pytest.raises(InvalidCSVError, match="empty column name at position 2"):
            validate_and_load_csv(csv_data, filename="data.csv")

    def test_rejects_duplicate_column_headers(self):
        csv_data = b"col1,col2,col1\n1,2,3\n"
        with pytest.raises(InvalidCSVError, match="duplicate column headers"):
            validate_and_load_csv(csv_data, filename="data.csv")

    def test_rejects_header_only_empty_data(self):
        csv_data = b"col1,col2,col3\n"
        with pytest.raises(InvalidCSVError, match="no data records"):
            validate_and_load_csv(csv_data, filename="data.csv")

    def test_rejects_oversized_file(self):
        large_bytes = b"a" * 1024
        with pytest.raises(FileTooLargeError):
            validate_and_load_csv(large_bytes, filename="data.csv", max_size_bytes=512)

    def test_rejects_excessive_row_count(self):
        csv_data = b"id,val\n1,a\n2,b\n3,c\n4,d\n5,e\n"
        with pytest.raises(LimitExceededError, match="row count"):
            validate_and_load_csv(csv_data, filename="data.csv", max_rows=3)

    def test_rejects_excessive_column_count(self):
        csv_data = b"a,b,c,d,e\n1,2,3,4,5\n"
        with pytest.raises(LimitExceededError, match="column count"):
            validate_and_load_csv(csv_data, filename="data.csv", max_cols=3)
