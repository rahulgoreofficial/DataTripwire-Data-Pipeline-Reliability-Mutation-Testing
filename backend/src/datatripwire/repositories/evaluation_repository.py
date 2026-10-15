"""Filesystem-backed repository for persisting and retrieving evaluation reports.

Stores full serialized EvaluationReport models using atomic writes and provides
dataset evaluation history listing.
"""

from datetime import datetime
import json
from pathlib import Path
import tempfile
from typing import List, Optional

from datatripwire.config import settings
from datatripwire.domain.models import EvaluationReport
from datatripwire.exceptions import EvaluationNotFoundError, StorageCorruptedError
from datatripwire.schemas import EvaluationSummaryItem


class EvaluationRepository:
    """Manages local filesystem storage for evaluation reports."""

    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or settings.evaluations_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _report_path(self, report_id: str) -> Path:
        return self.storage_dir / f"{report_id}.json"

    def exists(self, report_id: str) -> bool:
        """Check whether an evaluation report exists in storage."""
        return self._report_path(report_id).is_file()

    def save(self, report: EvaluationReport) -> EvaluationReport:
        """Persist an evaluation report atomically."""
        target_path = self._report_path(report.report_id)
        report_data = report.model_dump(mode="json")

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=self.storage_dir, delete=False) as tf:
            json.dump(report_data, tf, indent=2)
            temp_path = Path(tf.name)
        temp_path.replace(target_path)

        return report

    def get(self, report_id: str) -> EvaluationReport:
        """Retrieve an evaluation report by ID."""
        target_path = self._report_path(report_id)
        if not target_path.is_file():
            raise EvaluationNotFoundError(report_id)

        try:
            with open(target_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.pop("mutation_score", None)
            return EvaluationReport(**data)
        except Exception as e:
            raise StorageCorruptedError(str(target_path), str(e))

    def list_for_dataset(self, dataset_id: str) -> List[EvaluationSummaryItem]:
        """List summary records of evaluations belonging to a specific dataset."""
        summaries: List[EvaluationSummaryItem] = []
        for report_file in sorted(self.storage_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("dataset_id") == dataset_id:
                    summaries.append(
                        EvaluationSummaryItem(
                            report_id=data["report_id"],
                            dataset_id=data["dataset_id"],
                            created_at=datetime.fromisoformat(data["created_at"]),
                            total_attempted=data["total_attempted"],
                            successfully_applied=data["successfully_applied"],
                            detected_mutations=data["detected_mutations"],
                            surviving_mutations=data["surviving_mutations"],
                            failed_evaluations=data["failed_evaluations"],
                            mutation_score=data.get("mutation_score"),
                        )
                    )
            except Exception:
                continue
        return summaries
