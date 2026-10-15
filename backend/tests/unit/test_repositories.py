"""Unit tests for filesystem-backed repositories.

Verifies:
1. DatasetRepository save, get, dataframe retrieval, and listing.
2. EvaluationRepository save, get, and dataset history listing.
3. Clean exceptions for missing records and corrupted files.
"""

from datetime import datetime, timezone
from decimal import Decimal
import pytest

from datatripwire.domain.models import DatasetProfile, EvaluationReport
from datatripwire.exceptions import DatasetNotFoundError, EvaluationNotFoundError, StorageCorruptedError
from datatripwire.repositories.dataset_repository import DatasetRepository
from datatripwire.repositories.evaluation_repository import EvaluationRepository


class TestRepositories:
    """Test suite for repository storage operations."""

    def test_dataset_repository_lifecycle(self, tmp_path):
        repo = DatasetRepository(storage_dir=tmp_path / "datasets")
        profile = DatasetProfile(
            dataset_id="TEST-DS-01",
            filename="sales.csv",
            row_count=10,
            column_count=5,
            is_sales_compatible=True,
        )
        csv_bytes = b"transaction_id,customer_id,quantity,unit_price,transaction_date\nORD-1,C-1,1,100,2026-03-01\n"

        # Save
        saved = repo.save(
            dataset_id="TEST-DS-01",
            filename="sales.csv",
            csv_bytes=csv_bytes,
            profile=profile,
            is_sales_compatible=True,
        )
        assert saved.dataset_id == "TEST-DS-01"
        assert repo.exists("TEST-DS-01") is True

        # Get metadata
        retrieved = repo.get("TEST-DS-01")
        assert retrieved.filename == "sales.csv"
        assert retrieved.profile.row_count == 10

        # Get DataFrame
        df = repo.get_dataframe("TEST-DS-01")
        assert len(df) == 1
        assert df["transaction_id"].iloc[0] == "ORD-1"

        # List
        all_ds = repo.list_all()
        assert len(all_ds) == 1

    def test_dataset_repository_not_found(self, tmp_path):
        repo = DatasetRepository(storage_dir=tmp_path / "datasets")
        with pytest.raises(DatasetNotFoundError):
            repo.get("NONEXISTENT")

    def test_dataset_repository_corrupted_file(self, tmp_path):
        repo = DatasetRepository(storage_dir=tmp_path / "datasets")
        # Write corrupted JSON to metadata file
        meta_file = (tmp_path / "datasets") / "BAD-DS.meta.json"
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        meta_file.write_text("NOT_VALID_JSON{", encoding="utf-8")

        with pytest.raises(StorageCorruptedError):
            repo.get("BAD-DS")

    def test_evaluation_repository_lifecycle(self, tmp_path):
        repo = EvaluationRepository(storage_dir=tmp_path / "evals")
        report = EvaluationReport(
            report_id="REP-99",
            dataset_id="DS-01",
            created_at=datetime.now(timezone.utc),
            total_attempted=2,
            successfully_applied=2,
            detected_mutations=1,
            surviving_mutations=1,
            failed_evaluations=0,
        )

        repo.save(report)
        assert repo.exists("REP-99") is True

        retrieved = repo.get("REP-99")
        assert retrieved.report_id == "REP-99"
        assert retrieved.mutation_score == 50.0

        # List for dataset
        items = repo.list_for_dataset("DS-01")
        assert len(items) == 1
        assert items[0].report_id == "REP-99"

    def test_evaluation_repository_not_found(self, tmp_path):
        repo = EvaluationRepository(storage_dir=tmp_path / "evals")
        with pytest.raises(EvaluationNotFoundError):
            repo.get("NONEXISTENT-REPORT")
