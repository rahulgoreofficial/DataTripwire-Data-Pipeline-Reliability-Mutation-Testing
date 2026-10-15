"""FastAPI dependencies and service providers for DataTripwire.

Provides dependency injection for dataset repositories, evaluation repositories,
and evaluation services.
"""

from functools import lru_cache
from datatripwire.repositories.dataset_repository import DatasetRepository
from datatripwire.repositories.evaluation_repository import EvaluationRepository
from datatripwire.services.evaluator import EvaluationService


@lru_cache()
def get_dataset_repository() -> DatasetRepository:
    """Provide singleton instance of DatasetRepository."""
    return DatasetRepository()


@lru_cache()
def get_evaluation_repository() -> EvaluationRepository:
    """Provide singleton instance of EvaluationRepository."""
    return EvaluationRepository()


def get_evaluation_service() -> EvaluationService:
    """Provide EvaluationService instance."""
    return EvaluationService()
