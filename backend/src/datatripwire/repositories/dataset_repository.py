"""Filesystem-backed repository for persisting and retrieving datasets.

Maintains immutable storage of raw uploaded CSV files and their corresponding
metadata profiles. All writes use atomic temporary-file replacement.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import List, Optional
import pandas as pd

from datatripwire.config import settings
from datatripwire.domain.models import DatasetProfile
from datatripwire.exceptions import DatasetNotFoundError, StorageCorruptedError
from datatripwire.schemas import DatasetResponse


class DatasetRepository:
    """Manages local filesystem storage for ingested datasets."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or settings.datasets_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _csv_path(self, dataset_id: str) -> Path:
        return self.storage_dir / f"{dataset_id}.csv"

    def _meta_path(self, dataset_id: str) -> Path:
        return self.storage_dir / f"{dataset_id}.meta.json"

    def exists(self, dataset_id: str) -> bool:
        """Check whether a dataset exists in storage."""
        return self._csv_path(dataset_id).is_file() and self._meta_path(dataset_id).is_file()

    def save(
        self,
        dataset_id: str,
        filename: str,
        csv_bytes: bytes,
        profile: DatasetProfile,
        is_sales_compatible: bool,
        warnings: Optional[List[str]] = None,
        uploaded_at: Optional[datetime] = None,
    ) -> DatasetResponse:
        """Persist raw CSV bytes and profile metadata atomically."""
        upload_time = uploaded_at or datetime.now(timezone.utc)
        meta_dict = {
            "dataset_id": dataset_id,
            "filename": filename,
            "uploaded_at": upload_time.isoformat(),
            "is_sales_compatible": is_sales_compatible,
            "warnings": warnings or [],
            "profile": profile.model_dump(mode="json"),
        }

        csv_target = self._csv_path(dataset_id)
        meta_target = self._meta_path(dataset_id)

        # Write CSV atomically
        with tempfile.NamedTemporaryFile("wb", dir=self.storage_dir, delete=False) as tf:
            tf.write(csv_bytes)
            temp_csv = Path(tf.name)
        temp_csv.replace(csv_target)

        # Write Metadata atomically
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.storage_dir, delete=False) as tf:
            json.dump(meta_dict, tf, indent=2)
            temp_meta = Path(tf.name)
        temp_meta.replace(meta_target)

        return DatasetResponse(
            dataset_id=dataset_id,
            filename=filename,
            uploaded_at=upload_time,
            profile=profile,
            is_sales_compatible=is_sales_compatible,
            warnings=warnings or [],
        )

    def get(self, dataset_id: str) -> DatasetResponse:
        """Retrieve dataset metadata and profile."""
        meta_path = self._meta_path(dataset_id)
        if not meta_path.is_file():
            raise DatasetNotFoundError(dataset_id)

        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DatasetResponse(
                dataset_id=data["dataset_id"],
                filename=data["filename"],
                uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
                profile=DatasetProfile(**data["profile"]),
                is_sales_compatible=data["is_sales_compatible"],
                warnings=data.get("warnings", []),
            )
        except Exception as e:
            raise StorageCorruptedError(str(meta_path), str(e))

    def get_dataframe(self, dataset_id: str) -> pd.DataFrame:
        """Load and return an immutable copy of the dataset as a pandas DataFrame."""
        csv_path = self._csv_path(dataset_id)
        if not csv_path.is_file():
            raise DatasetNotFoundError(dataset_id)

        try:
            # Preserve identifier strings (e.g. leading zeros) by specifying dtype as object for ID columns
            return pd.read_csv(csv_path, dtype={"transaction_id": str, "customer_id": str})
        except Exception as e:
            raise StorageCorruptedError(str(csv_path), str(e))

    def get_csv_bytes(self, dataset_id: str) -> bytes:
        """Retrieve raw CSV bytes."""
        csv_path = self._csv_path(dataset_id)
        if not csv_path.is_file():
            raise DatasetNotFoundError(dataset_id)
        return csv_path.read_bytes()

    def list_all(self) -> List[DatasetResponse]:
        """List all persisted datasets."""
        results: List[DatasetResponse] = []
        for meta_file in sorted(self.storage_dir.glob("*.meta.json")):
            dataset_id = meta_file.name.replace(".meta.json", "")
            try:
                results.append(self.get(dataset_id))
            except Exception:
                continue
        return results
