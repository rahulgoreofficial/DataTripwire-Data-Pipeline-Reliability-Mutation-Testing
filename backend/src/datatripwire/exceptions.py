"""Domain and application exceptions for DataTripwire.

Defines a clean exception hierarchy for consistent API error handling.
"""

from typing import Optional


class DataTripwireError(Exception):
    """Base exception for all DataTripwire errors."""

    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


class DatasetNotFoundError(DataTripwireError):
    """Raised when a requested dataset identifier does not exist."""

    def __init__(self, dataset_id: str):
        super().__init__(f"Dataset with ID '{dataset_id}' not found.", code="DATASET_NOT_FOUND")
        self.dataset_id = dataset_id


class EvaluationNotFoundError(DataTripwireError):
    """Raised when a requested evaluation report identifier does not exist."""

    def __init__(self, evaluation_id: str):
        super().__init__(f"Evaluation with ID '{evaluation_id}' not found.", code="EVALUATION_NOT_FOUND")
        self.evaluation_id = evaluation_id


class InvalidCSVError(DataTripwireError):
    """Raised when an uploaded CSV is malformed, empty, or structurally invalid."""

    def __init__(self, message: str, code: str = "INVALID_CSV"):
        super().__init__(message, code=code)


class FileTooLargeError(DataTripwireError):
    """Raised when an uploaded file exceeds the configured size limit."""

    def __init__(self, size_bytes: int, max_bytes: int):
        super().__init__(
            f"File size of {size_bytes} bytes exceeds the maximum limit of {max_bytes} bytes.",
            code="FILE_TOO_LARGE",
        )


class LimitExceededError(DataTripwireError):
    """Raised when dataset dimensions exceed row or column limits."""

    def __init__(self, message: str):
        super().__init__(message, code="LIMIT_EXCEEDED")


class IncompatibleSchemaError(DataTripwireError):
    """Raised when an evaluation requires canonical sales columns not present in the dataset."""

    def __init__(self, missing_columns: list):
        super().__init__(
            f"Dataset is not compatible with sales evaluation. Missing required columns: {missing_columns}",
            code="INCOMPATIBLE_SALES_SCHEMA",
        )
        self.missing_columns = missing_columns


class MutationApplicationError(DataTripwireError):
    """Raised when a mutation cannot be meaningfully applied to a dataset."""

    def __init__(self, message: str, code: str = "MUTATION_APPLICATION_FAILED"):
        super().__init__(message, code=code)


class StorageCorruptedError(DataTripwireError):
    """Raised when persisted dataset files or evaluation records cannot be loaded."""

    def __init__(self, path: str, reason: str):
        super().__init__(f"Stored object at '{path}' is corrupted: {reason}", code="STORAGE_CORRUPTED")
