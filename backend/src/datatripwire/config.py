"""Configuration, settings, and schema definitions for DataTripwire.

Centralizes paths, default schema expectations, column specifications, runtime storage,
and environment settings.
"""

import os
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, Field


# Base directory paths
PACKAGE_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = PACKAGE_ROOT.parent.parent
WORKSPACE_ROOT = BACKEND_ROOT.parent
DATA_DIR = PACKAGE_ROOT / "data"
SAMPLE_SALES_CSV = DATA_DIR / "sample_sales.csv"
SAMPLE_MANUFACTURING_CSV = DATA_DIR / "sample_manufacturing.csv"

# Schema expectations for initial sales dataset
SALES_SCHEMA_COLUMNS: List[str] = [
    "transaction_id",
    "customer_id",
    "quantity",
    "unit_price",
    "transaction_date",
]

# Primary identifier column
PRIMARY_KEY_COLUMN: str = "transaction_id"

# Inferred column type representations
SALES_COLUMN_TYPES: Dict[str, str] = {
    "transaction_id": "string",
    "customer_id": "string",
    "quantity": "integer",
    "unit_price": "float",
    "transaction_date": "date",
}

# Manufacturing / Industrial IoT schema expectations
MANUFACTURING_SCHEMA_COLUMNS: List[str] = [
    "reading_id",
    "timestamp",
    "facility_id",
    "machine_id",
    "production_line",
    "product_family",
    "batch_id",
    "shift",
    "temperature_c",
    "pressure_bar",
    "vibration_mm_s",
    "motor_current_a",
    "power_kw",
    "energy_kwh_20min",
    "units_produced",
    "defect_count",
    "quality_pass_rate_pct",
    "machine_status",
]

# Essential columns required for manufacturing validation & testing
MANUFACTURING_REQUIRED_COLUMNS: List[str] = [
    "reading_id",
    "timestamp",
    "machine_id",
    "temperature_c",
    "pressure_bar",
    "vibration_mm_s",
    "units_produced",
    "defect_count",
]

MANUFACTURING_PRIMARY_KEY: str = "reading_id"

# Documented baseline expectations for sample_sales.csv
SAMPLE_DATASET_BASELINE = {
    "filename": "sample_sales.csv",
    "row_count": 15,
    "column_count": 5,
    "unique_customer_count": 10,
    "expected_revenue": "19000.00",
    "expected_transaction_count": 15,
}


class Settings(BaseModel):
    """Runtime application configuration with safe local defaults."""

    app_name: str = "DataTripwire"
    app_version: str = "0.1.0"
    env: str = Field(default_factory=lambda: os.getenv("DATATRIPWIRE_ENV", "development"))
    log_level: str = Field(default_factory=lambda: os.getenv("DATATRIPWIRE_LOG_LEVEL", "INFO"))

    # Server settings
    host: str = Field(default_factory=lambda: os.getenv("BACKEND_HOST", "127.0.0.1"))
    port: int = Field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "8000")))

    # File and dimension limits
    max_upload_size_bytes: int = Field(
        default_factory=lambda: int(os.getenv("DATATRIPWIRE_MAX_UPLOAD_SIZE", str(5 * 1024 * 1024)))  # 5 MB
    )
    max_accepted_rows: int = Field(
        default_factory=lambda: int(os.getenv("DATATRIPWIRE_MAX_ROWS", "50000"))
    )
    max_accepted_columns: int = Field(
        default_factory=lambda: int(os.getenv("DATATRIPWIRE_MAX_COLUMNS", "100"))
    )
    max_mutations_per_request: int = Field(
        default_factory=lambda: int(os.getenv("DATATRIPWIRE_MAX_MUTATIONS", "10"))
    )

    # Runtime storage directories
    runtime_data_dir: Path = Field(
        default_factory=lambda: Path(
            os.getenv("DATATRIPWIRE_RUNTIME_DIR", str(WORKSPACE_ROOT / "data" / "runtime"))
        ).resolve()
    )

    # CORS origins
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv(
                "DATATRIPWIRE_CORS_ORIGINS",
                "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
            ).split(",")
            if origin.strip()
        ]
    )

    @property
    def datasets_dir(self) -> Path:
        """Directory for persisting uploaded CSV files and dataset metadata."""
        path = self.runtime_data_dir / "datasets"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def evaluations_dir(self) -> Path:
        """Directory for persisting evaluation reports."""
        path = self.runtime_data_dir / "evaluations"
        path.mkdir(parents=True, exist_ok=True)
        return path


# Singleton default settings
settings = Settings()
