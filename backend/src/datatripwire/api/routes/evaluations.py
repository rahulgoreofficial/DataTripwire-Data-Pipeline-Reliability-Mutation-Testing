"""Evaluation execution and report retrieval endpoints for DataTripwire."""

from fastapi import APIRouter, Depends
from datatripwire.api.dependencies import (
    get_dataset_repository,
    get_evaluation_repository,
    get_evaluation_service,
)
from datatripwire.domain.models import EvaluationReport
from datatripwire.repositories.dataset_repository import DatasetRepository
from datatripwire.repositories.evaluation_repository import EvaluationRepository
from datatripwire.schemas import EvaluationCreateRequest
from datatripwire.services.evaluator import EvaluationService

router = APIRouter(tags=["Evaluations"])


@router.post("/api/v1/datasets/{dataset_id}/evaluations", response_model=EvaluationReport, status_code=201)
def run_evaluation(
    dataset_id: str,
    payload: EvaluationCreateRequest,
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
    eval_repo: EvaluationRepository = Depends(get_evaluation_repository),
    eval_service: EvaluationService = Depends(get_evaluation_service),
):
    """Execute a batch of synthetic mutations and validation rules against a dataset.
    
    Each mutation is applied independently to a fresh copy of the clean dataset.
    Detection is derived from actual validation findings compared with baseline findings.
    Surviving mutations produce deterministic rule recommendations.
    """
    # Load immutable original dataset
    df = dataset_repo.get_dataframe(dataset_id)

    # Execute evaluation
    report = eval_service.evaluate_dataset(
        df=df,
        dataset_id=dataset_id,
        mutations=payload.mutations,
        rules=payload.rules,
        domain=payload.domain,
    )

    # Persist and return report
    eval_repo.save(report)
    return report


@router.get("/api/v1/evaluations/{evaluation_id}", response_model=EvaluationReport)
def get_evaluation_report(
    evaluation_id: str,
    eval_repo: EvaluationRepository = Depends(get_evaluation_repository),
):
    """Retrieve an evaluation report by ID."""
    return eval_repo.get(evaluation_id)
