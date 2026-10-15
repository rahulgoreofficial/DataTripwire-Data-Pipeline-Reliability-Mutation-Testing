"""CSV loader and validator service for DataTripwire.

Performs robust, bounded validation of incoming CSV files before parsing:
- File size, encoding, and extension validation
- Header validation (missing, empty, or duplicate column names)
- Malformed rows and structural irregularities
- Dimension boundary checks (max rows, max columns)
- Preserves raw string representations for identifier columns (e.g., leading zeros)
"""

import csv
import io
from pathlib import Path
from typing import List, Tuple, Union
import pandas as pd

from datatripwire.config import settings
from datatripwire.exceptions import FileTooLargeError, InvalidCSVError, LimitExceededError


def validate_and_load_csv(
    file_source: Union[bytes, str, Path],
    filename: str = "upload.csv",
    max_size_bytes: int = settings.max_upload_size_bytes,
    max_rows: int = settings.max_accepted_rows,
    max_cols: int = settings.max_accepted_columns,
) -> Tuple[pd.DataFrame, bytes, List[str]]:
    """Validate and parse a CSV file source into a pandas DataFrame.
    
    Args:
        file_source: Raw bytes or filesystem path to CSV.
        filename: Original filename descriptor.
        max_size_bytes: Upper byte limit.
        max_rows: Upper row limit.
        max_cols: Upper column limit.
        
    Returns:
        Tuple of (DataFrame, raw_bytes, list_of_warnings).
        
    Raises:
        InvalidCSVError, FileTooLargeError, LimitExceededError
    """
    warnings: List[str] = []

    # 1. Validate file extension
    if not filename.lower().endswith(".csv"):
        raise InvalidCSVError(f"Unsupported file extension for '{filename}'. Only .csv files are supported.")

    # 2. Extract and validate byte size
    if isinstance(file_source, bytes):
        raw_bytes = file_source
    else:
        path = Path(file_source)
        if not path.is_file():
            raise InvalidCSVError(f"CSV file not found at '{path}'.")
        raw_bytes = path.read_bytes()

    if len(raw_bytes) == 0:
        raise InvalidCSVError("The uploaded CSV file is empty (0 bytes).")

    if len(raw_bytes) > max_size_bytes:
        raise FileTooLargeError(len(raw_bytes), max_size_bytes)

    # 3. Decode text with encoding fallback
    decoded_text: str = ""
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            decoded_text = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if not decoded_text.strip():
        raise InvalidCSVError("The CSV file contains only whitespace or could not be decoded.")

    # 4. Inspect headers with standard csv.reader
    text_stream = io.StringIO(decoded_text)
    try:
        reader = csv.reader(text_stream)
        header_row = next(reader, None)
    except Exception as e:
        raise InvalidCSVError(f"Failed to parse CSV structure: {str(e)}")

    if header_row is None or len(header_row) == 0:
        raise InvalidCSVError("CSV file is missing a header row.")

    # Check for empty or duplicate column names
    cleaned_headers = [col.strip() for col in header_row]
    for idx, col in enumerate(cleaned_headers):
        if not col:
            raise InvalidCSVError(f"Header row contains an empty column name at position {idx + 1}.")

    if len(cleaned_headers) != len(set(cleaned_headers)):
        seen = set()
        duplicates = set()
        for col in cleaned_headers:
            if col in seen:
                duplicates.add(col)
            seen.add(col)
        raise InvalidCSVError(f"CSV contains duplicate column headers: {sorted(list(duplicates))}")

    if len(cleaned_headers) > max_cols:
        raise LimitExceededError(
            f"CSV column count ({len(cleaned_headers)}) exceeds the maximum allowed ({max_cols})."
        )

    # 5. Parse into DataFrame with pandas
    # Force ID columns to object/str so leading zeros and alphanumeric IDs are preserved
    dtype_spec = {"transaction_id": str, "customer_id": str}
    try:
        text_stream.seek(0)
        df = pd.read_csv(text_stream, dtype=dtype_spec)
    except Exception as e:
        raise InvalidCSVError(f"Malformed CSV tabular structure: {str(e)}")

    # Strip column name whitespace in DataFrame
    df.columns = df.columns.str.strip()

    if len(df) == 0:
        raise InvalidCSVError("CSV contains headers but no data records (empty dataset).")

    if len(df) > max_rows:
        raise LimitExceededError(f"CSV row count ({len(df)}) exceeds the maximum allowed ({max_rows}).")

    return df, raw_bytes, warnings
