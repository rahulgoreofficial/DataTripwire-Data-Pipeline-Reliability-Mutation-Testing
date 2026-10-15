"""Dataset management endpoints for DataTripwire.

Supports sample dataset loading, CSV uploads, profile inspection, and evaluation history.
"""

from typing import List
import uuid
from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import JSONResponse

from datatripwire.api.dependencies import get_dataset_repository, get_evaluation_repository
from datatripwire.config import SAMPLE_MANUFACTURING_CSV, SAMPLE_SALES_CSV
from datatripwire.domains.registry import get_domain_registry
from datatripwire.domain.models import DatasetProfile
from datatripwire.exceptions import InvalidCSVError
from datatripwire.repositories.dataset_repository import DatasetRepository
from datatripwire.repositories.evaluation_repository import EvaluationRepository
from datatripwire.schemas import DatasetResponse, EvaluationSummaryItem
from datatripwire.services.csv_loader import validate_and_load_csv
from datatripwire.services.profiler import profile_dataframe

router = APIRouter(prefix="/api/v1/datasets", tags=["Datasets"])


@router.post("/sample", response_model=DatasetResponse, status_code=201)
def load_sample_dataset(
    domain: str = "sales",
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """Load a bundled deterministic sample dataset (sales or manufacturing)."""
    if domain.lower() in ("manufacturing", "mfg", "iot"):
        csv_file = SAMPLE_MANUFACTURING_CSV
        dataset_id = "sample-manufacturing"
        filename = "sample_manufacturing.csv"
    else:
        csv_file = SAMPLE_SALES_CSV
        dataset_id = "sample-sales"
        filename = "sample_sales.csv"

    if not csv_file.is_file():
        raise InvalidCSVError(f"Bundled sample dataset file '{filename}' is missing from backend package.")

    df, raw_bytes, warnings = validate_and_load_csv(
        file_source=csv_file,
        filename=filename,
    )

    profile = profile_dataframe(df, dataset_id=dataset_id, filename=filename)

    response = dataset_repo.save(
        dataset_id=dataset_id,
        filename=filename,
        csv_bytes=raw_bytes,
        profile=profile,
        is_sales_compatible=profile.is_sales_compatible,
        warnings=warnings + profile.warnings,
    )
    return response


@router.post("/sample-manufacturing", response_model=DatasetResponse, status_code=201)
def load_sample_manufacturing_dataset(
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """Convenience endpoint to load the bundled deterministic manufacturing IoT dataset."""
    return load_sample_dataset(domain="manufacturing", dataset_repo=dataset_repo)


@router.post("", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(..., description="CSV file to upload and profile"),
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """Upload and profile a custom CSV dataset.
    
    Validates file headers, row/column boundaries, and checks schema compatibility
    with the sales mutation testing engine.
    """
    filename = file.filename or "uploaded.csv"
    if not filename.lower().endswith(".csv"):
        raise InvalidCSVError(f"Unsupported file format for '{filename}'. Only .csv files are supported.")

    content = await file.read()
    if len(content) == 0:
        raise InvalidCSVError("Uploaded file is empty (0 bytes).")

    df, raw_bytes, warnings = validate_and_load_csv(
        file_source=content,
        filename=filename,
    )

    dataset_id = f"ds-{uuid.uuid4().hex[:8]}"
    profile = profile_dataframe(df, dataset_id=dataset_id, filename=filename)

    response = dataset_repo.save(
        dataset_id=dataset_id,
        filename=filename,
        csv_bytes=raw_bytes,
        profile=profile,
        is_sales_compatible=profile.is_sales_compatible,
        warnings=warnings + profile.warnings,
    )
    return response


@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """List all persisted datasets."""
    return dataset_repo.list_all()


@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: str,
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """Retrieve metadata and profile for a specific dataset."""
    return dataset_repo.get(dataset_id)


@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
def get_dataset_profile(
    dataset_id: str,
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """Retrieve the structural profile and summary statistics for a dataset."""
    dataset = dataset_repo.get(dataset_id)
    return dataset.profile


@router.get("/{dataset_id}/evaluations", response_model=List[EvaluationSummaryItem])
def list_dataset_evaluations(
    dataset_id: str,
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
    eval_repo: EvaluationRepository = Depends(get_evaluation_repository),
):
    """List historical evaluation runs executed against a specific dataset."""
    # Verify dataset exists
    dataset_repo.get(dataset_id)
    return eval_repo.list_for_dataset(dataset_id)


@router.get("/{dataset_id}/domains")
def get_dataset_domains(
    dataset_id: str,
    dataset_repo: DatasetRepository = Depends(get_dataset_repository),
):
    """Retrieve supported domain profiles and their compatibility for a dataset."""
    df = dataset_repo.get_dataframe(dataset_id)
    registry = get_domain_registry()
    detected = registry.detect_domain(df)
    return {
        "dataset_id": dataset_id,
        "detected_domain": detected.domain_id,
        "domains": registry.list_domains(df),
    }
